import asyncio
import json
import logging
from typing import AsyncIterable, Callable, Any, List, Dict

logger = logging.getLogger(__name__)

class StreamingFunctionComposer:
    """
    Implements the Streaming Function Composition pattern.
    Pipes output chunks (tokens/steps) from one module (e.g., Phoenix Planner)
    directly into the input of another module (e.g., Hive Executor)
    in real-time before the full generation completes.
    """
    def __init__(self, max_buffer_size: int = 65536):
        self.buffer = ""
        self.max_buffer_size = max_buffer_size

    async def pipe_steps(
        self, 
        token_stream: AsyncIterable[str], 
        step_handler: Callable[[Dict[str, Any]], Any]
    ) -> List[Any]:
        """
        Parses incoming JSON step definitions from a stream and
        triggers execution of completed steps eagerly.
        """
        results = []
        
        async for token in token_stream:
            self.buffer += token
            
            # Prevent OOM buffer overflow attacks
            if len(self.buffer) > self.max_buffer_size:
                raise ValueError(f"Streaming buffer overflow: exceeded limit of {self.max_buffer_size} bytes without complete step.")
            
            # Eager step parsing logic
            # Look for step definitions in format: "STEP: { ... JSON ... }"
            while "STEP:" in self.buffer:
                parts = self.buffer.split("STEP:", 1)
                remaining = parts[1].strip()
                
                # Robust bracket counter tracking string literals and escapes
                in_string = False
                escape = False
                bracket_count = 0
                json_str = ""
                end_index = -1
                
                for idx, char in enumerate(remaining):
                    if escape:
                        escape = False
                        if bracket_count > 0:
                            json_str += char
                        continue
                        
                    if char == "\\":
                        escape = True
                        if bracket_count > 0:
                            json_str += char
                        continue
                        
                    if char == '"':
                        in_string = not in_string
                        if bracket_count > 0:
                            json_str += char
                        continue
                        
                    if not in_string:
                        if char == "{":
                            bracket_count += 1
                        elif char == "}":
                            bracket_count -= 1
                            
                    if bracket_count > 0:
                        json_str += char
                    elif bracket_count == 0 and json_str:
                        # Append the closing bracket
                        json_str += "}"
                        end_index = idx
                        break
                        
                if end_index != -1:
                    # Successfully parsed a complete step JSON block
                    try:
                        step_data = json.loads(json_str)
                        logger.info(f"streaming_composer: Parsed eager step: {step_data.get('name')}")
                        
                        # Eagerly invoke the handler (e.g., Hive Executor command)
                        step_res = await step_handler(step_data)
                        results.append({
                            "step": step_data.get("name"),
                            "result": step_res
                        })
                    except Exception as e:
                        logger.error(f"streaming_composer: Failed to parse step JSON: {e}. Content: {json_str}")
                    
                    # Advance buffer past parsed step
                    self.buffer = remaining[end_index+1:]
                else:
                    # JSON not fully loaded yet, wait for more tokens
                    break
                    
        return results
