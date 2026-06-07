import json
import os
from typing import Dict, Any, Optional

def load_trace(strategy: str, problem_id: int, trace_dir: str = "traces") -> Optional[Dict]:
    """根据策略和问题ID加载完整 trace"""
    filename = os.path.join(trace_dir, f"{strategy}_full.jsonl")
    if not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if data["problem_id"] == problem_id and data["strategy"] == strategy:
                return data
    return None

def replay_problem(strategy_name: str, problem: str, problem_id: int, strategy_instance):
    """使用给定的策略实例重放问题"""
    result = strategy_instance.solve(problem, problem_id)
    return result