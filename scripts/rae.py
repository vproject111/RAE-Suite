#!/usr/bin/env python3
import sys
import os
import json
import argparse
from typing import List, Dict, Any

# Discovery of core/path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(PROJECT_ROOT)

from core.tool_gateway import ToolGateway
from rae_contracts import RiskClass

def read_replay_log(log_path: str = "trajectory_replay.jsonl") -> List[Dict[str, Any]]:
    events = []
    if not os.path.exists(log_path):
        return events
    with open(log_path, "r") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return events

def run_inspect(args):
    print("=== RAE TRAJECTORY INSPECTOR ===")
    events = read_replay_log()
    if not events:
        print("No recorded trajectories found.")
        return
        
    traces = {}
    for ev in events:
        t_id = ev.get("trace_id", "unknown")
        if t_id not in traces:
            traces[t_id] = []
        traces[t_id].append(ev)
        
    print(f"Total Trajectories: {len(traces)}")
    for t_id, steps in traces.items():
        print(f"\nTrace: {t_id}")
        for i, st in enumerate(steps):
            cmd = " ".join(st.get("command", []))
            status = "SUCCESS" if st.get("exit_code") == 0 else "FAILED"
            print(f"  Step {i+1}: {cmd} -> {status} (Exit: {st.get('exit_code')})")

def run_replay(args):
    trace_id = args.trace_id
    print(f"=== REPLAYING TRAJECTORY: {trace_id} ===")
    events = read_replay_log()
    trace_steps = [e for e in events if e.get("trace_id") == trace_id]
    
    if not trace_steps:
        print(f"Error: No events found for trace {trace_id}")
        sys.exit(1)
        
    gateway = ToolGateway(".")
    for i, step in enumerate(trace_steps):
        cmd = step.get("command", [])
        print(f"\nReplaying Step {i+1}: {' '.join(cmd)}")
        rc_str = step.get("risk_class", "R0")
        try:
            rc = RiskClass[rc_str]
        except KeyError:
            rc = RiskClass.R0
        exit_code, stdout, stderr = gateway.execute_tool(
            trace_id=trace_id,
            command=cmd,
            cwd=".",
            risk_class=rc
        )
        print(f"Exit Code: {exit_code}")
        if stdout:
            print(f"STDOUT:\n{stdout}")
        if stderr:
            print(f"STDERR:\n{stderr}")

def run_fork(args):
    trace_id = args.trace_id
    step_num = args.from_step
    print(f"=== FORKING TRAJECTORY: {trace_id} FROM STEP {step_num} ===")
    events = read_replay_log()
    trace_steps = [e for e in events if e.get("trace_id") == trace_id]
    
    if not trace_steps:
        print(f"Error: No events found for trace {trace_id}")
        sys.exit(1)
        
    if step_num > len(trace_steps) or step_num < 1:
        print(f"Error: Step number {step_num} is out of bounds (1 to {len(trace_steps)})")
        sys.exit(1)
        
    # Replay up to step N-1
    gateway = ToolGateway(".")
    print(f"Restoring state by replaying up to step {step_num - 1}...")
    for i in range(step_num - 1):
        step = trace_steps[i]
        cmd = step.get("command", [])
        print(f"  Running setup step {i+1}: {' '.join(cmd)}")
        rc_str = step.get("risk_class", "R0")
        try:
            rc = RiskClass[rc_str]
        except KeyError:
            rc = RiskClass.R0
        exit_code, _, stderr = gateway.execute_tool(trace_id=trace_id, command=cmd, cwd=".", risk_class=rc)
        if exit_code != 0:
            print(f"Error: Setup step {i+1} failed with exit code {exit_code}. Aborting fork. STDERR:\n{stderr}")
            sys.exit(1)
        
    # Fork point reached
    forked_step = trace_steps[step_num - 1]
    print(f"\n✅ Fork state established at step {step_num}.")
    print(f"Original command at this step was: {' '.join(forked_step.get('command', []))}")
    print("Sandbox is ready for interactive debug / modified execution.")

def main():
    parser = argparse.ArgumentParser(description="RAE CLI Tool for Trajectory Replay & Forking")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # inspect command
    subparsers.add_parser("inspect", help="Inspect all recorded trajectories")
    
    # replay command
    parser_replay = subparsers.add_parser("replay", help="Replay a specific trajectory")
    parser_replay.add_argument("trace_id", type=str, help="The trace ID to replay")
    
    # fork command
    parser_fork = subparsers.add_parser("fork", help="Fork a trajectory from a specific step")
    parser_fork.add_argument("trace_id", type=str, help="The trace ID to fork")
    parser_fork.add_argument("--from-step", type=int, required=True, help="Step number (1-indexed) to fork from")
    
    args = parser.parse_args()
    
    if args.command == "inspect":
        run_inspect(args)
    elif args.command == "replay":
        run_replay(args)
    elif args.command == "fork":
        run_fork(args)

if __name__ == "__main__":
    main()
