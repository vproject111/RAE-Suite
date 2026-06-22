import ast
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class TestIntegrityGuard:
    """
    AST-based guard that prevents agents from weakening tests.
    Detects deletion of assertions, addition of 'pass', or skipping critical tests.
    """
    def __init__(self):
        self.suspicious_patterns = [
            "pass",
            "pytest.skip",
            "unittest.skip",
            "pytest.xfail"
        ]

    def verify_integrity(self, original_code: str, modified_code: str) -> Tuple[bool, List[str]]:
        """
        Compares original and modified test code to detect weakening.
        """
        violations = []
        
        try:
            original_tree = ast.parse(original_code)
            modified_tree = ast.parse(modified_code)
        except SyntaxError as e:
            return False, [f"Syntax error in code: {e}"]

        # 1. Count Assertions
        original_asserts = self._count_nodes(original_tree, ast.Assert)
        modified_asserts = self._count_nodes(modified_tree, ast.Assert)
        
        if modified_asserts < original_asserts:
            violations.append(f"Assertion weakening detected: {original_asserts} -> {modified_asserts} asserts.")

        # 2. Detect Suspicious "pass" blocks in formerly active functions
        if self._has_new_pass_blocks(original_tree, modified_tree):
             violations.append("New 'pass' blocks detected in test functions, indicating logic removal.")

        # 3. Detect new skip decorators
        original_skips = self._count_skips(original_tree)
        modified_skips = self._count_skips(modified_tree)
        
        if modified_skips > original_skips:
            violations.append(f"Test skipping detected: {original_skips} -> {modified_skips} skips.")

        return (len(violations) == 0), violations

    def _count_nodes(self, tree, node_type):
        return len([node for node in ast.walk(tree) if isinstance(node, node_type)])

    def _count_skips(self, tree):
        count = 0
        for node in ast.walk(tree):
            # Check for @pytest.mark.skip or similar
            if isinstance(node, ast.Attribute) and node.attr in ["skip", "xfail"]:
                count += 1
            # Check for pytest.skip() calls
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ["skip", "xfail"]:
                count += 1
        return count

    def _has_new_pass_blocks(self, original_tree, modified_tree):
        # Simplified: check if any function body changed to just 'pass'
        orig_funcs = {n.name: n for n in ast.walk(original_tree) if isinstance(n, ast.FunctionDef)}
        mod_funcs = {n.name: n for n in ast.walk(modified_tree) if isinstance(n, ast.FunctionDef)}
        
        for name, mod_func in mod_funcs.items():
            if name in orig_funcs:
                # If modified function body is just 'pass' but original wasn't
                if len(mod_func.body) == 1 and isinstance(mod_func.body[0], ast.Pass):
                    if not (len(orig_funcs[name].body) == 1 and isinstance(orig_funcs[name].body[0], ast.Pass)):
                        return True
        return False
