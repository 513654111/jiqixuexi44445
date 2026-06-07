from typing import Dict, Any, List
from config import COST_PER_1K_INPUT, COST_PER_1K_OUTPUT

def estimate_cost(trace: List[Dict]) -> float:
    """根据 trace 中的 token usage 估算总成本（美元）"""
    total_input = 0
    total_output = 0
    for event in trace:
        usage = event.get("token_usage", {})
        total_input += usage.get("prompt", 0)
        total_output += usage.get("completion", 0)
    cost = (total_input / 1000) * COST_PER_1K_INPUT + (total_output / 1000) * COST_PER_1K_OUTPUT
    return cost

def aggregate_costs(results: List[Dict]) -> Dict[str, float]:
    """汇总多个结果的成本"""
    total_cost = 0.0
    total_input = 0
    total_output = 0
    for res in results:
        trace = res.get("trace", [])
        for event in trace:
            usage = event.get("token_usage", {})
            total_input += usage.get("prompt", 0)
            total_output += usage.get("completion", 0)
    total_cost = (total_input / 1000) * COST_PER_1K_INPUT + (total_output / 1000) * COST_PER_1K_OUTPUT
    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_cost_usd": total_cost
    }