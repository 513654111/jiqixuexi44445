import json
import random
from tqdm import tqdm
from typing import Dict, List, Any
from strategies import ReActStrategy, PlanExecuteStrategy, SelfConsistencyStrategy
from eval.dataset import load_gsm8k_subset
from eval.metrics import accuracy, bootstrap_ci, win_matrix
from observability.trace import TraceLogger
from observability.cost import aggregate_costs
from config import EVAL_DATASET_SIZE, SEED

def evaluate_strategy(strategy, dataset: List[Dict], logger: TraceLogger) -> List[Dict]:
    """评估单个策略，返回结果列表（每个问题一个字典）"""
    results = []
    for idx, item in enumerate(tqdm(dataset, desc=f"Evaluating {strategy.name}")):
        problem = item["question"]
        truth = item["answer"]
        output = strategy.solve(problem, problem_id=idx)
        pred = output["answer"]
        is_correct = (pred is not None and abs(pred - truth) < 1e-6)
        results.append({
            "problem_id": idx,
            "question": problem,
            "ground_truth": truth,
            "predicted": pred,
            "correct": is_correct,
            "trace": output.get("trace", [])
        })
        # 记录完整 trace
        logger.log_full_trace(strategy.name, idx, output.get("trace", []), pred)
        # 逐事件记录（可选）
        for event in output.get("trace", []):
            logger.log_event(strategy.name, idx, event)
    return results

def main():
    random.seed(SEED)
    print("=== Agentic Reasoning Lab Evaluation ===\n")

    # 加载数据集
    print("Loading dataset...")
    dataset = load_gsm8k_subset("gsm8k_test.jsonl", size=EVAL_DATASET_SIZE, seed=SEED)
    if not dataset:
        print("Warning: Using mock dataset. Place gsm8k_test.jsonl in root for real data.")
    else:
        print(f"Loaded {len(dataset)} problems from GSM8K")

    # 初始化策略
    strategies = [
        ReActStrategy(),
        PlanExecuteStrategy(),
        SelfConsistencyStrategy()
    ]

    logger = TraceLogger()
    all_results = {}

    # 评估每个策略
    for strategy in strategies:
        print(f"\n--- Evaluating {strategy.name} ---")
        results = evaluate_strategy(strategy, dataset, logger)
        all_results[strategy.name] = results

        # 计算准确率和置信区间
        acc = accuracy(results)
        correct_list = [r["correct"] for r in results]
        ci_lower, ci_upper = bootstrap_ci(correct_list)
        print(f"Accuracy: {acc:.1%} ({sum(correct_list)}/{len(results)})")
        print(f"95% CI (bootstrap): [{ci_lower:.1%}, {ci_upper:.1%}]")

        # 成本统计
        costs = aggregate_costs(results)
        print(f"Total cost: ${costs['total_cost_usd']:.4f}")
        print(f"Cost per correct answer: ${costs['total_cost_usd'] / max(1, sum(correct_list)):.4f}")

    # 计算胜率矩阵
    print("\n=== Win Matrix (Row beats Column) ===")
    matrix = win_matrix(all_results)
    for s1, row in matrix.items():
        print(f"{s1}: {row}")

    # 保存最终结果
    summary = {
        "dataset_size": len(dataset),
        "seed": SEED,
        "strategies": {}
    }
    for name, results in all_results.items():
        correct = sum(r["correct"] for r in results)
        acc = correct / len(results)
        ci_lower, ci_upper = bootstrap_ci([r["correct"] for r in results])
        costs = aggregate_costs(results)
        summary["strategies"][name] = {
            "accuracy": acc,
            "correct": correct,
            "total": len(results),
            "ci_95": [ci_lower, ci_upper],
            "cost_usd": costs["total_cost_usd"],
            "input_tokens": costs["input_tokens"],
            "output_tokens": costs["output_tokens"],
            "cost_per_correct": costs["total_cost_usd"] / max(1, correct)
        }
    with open("eval_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nEvaluation summary saved to eval_summary.json")
    print("Traces saved to traces/ directory")

if __name__ == "__main__":
    main()