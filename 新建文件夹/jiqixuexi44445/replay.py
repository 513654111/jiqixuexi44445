#!/usr/bin/env python
"""
Replay a specific problem using a given strategy.
Usage:
    python replay.py <strategy_keyword> <problem_id>
Example:
    python replay.py Self 3
    python replay.py ReAct 5
    python replay.py Plan 2
"""

import sys
import json
import os
from strategies import ReActStrategy, PlanExecuteStrategy, SelfConsistencyStrategy
from eval.dataset import load_gsm8k_subset

def load_dataset():
    """加载 GSM8K 数据集（与 run_eval.py 保持一致）"""
    # 优先从真实文件加载，否则使用模拟数据
    try:
        dataset = load_gsm8k_subset("gsm8k_test.jsonl", size=100)  # 取多一些以便索引
        if not dataset:
            raise FileNotFoundError
        return dataset
    except FileNotFoundError:
        print("Warning: gsm8k_test.jsonl not found, using mock dataset")
        from eval.dataset import load_gsm8k_subset as load_mock
        return load_mock("", size=10)  # 返回模拟数据

def load_original_trace(strategy_name, problem_id):
    """从 traces/ 目录中加载原始 trace（如果存在）"""
    trace_file = f"traces/{strategy_name}_full.jsonl"
    if not os.path.exists(trace_file):
        # 尝试去除括号版本
        simple_name = strategy_name.split('(')[0]
        trace_file = f"traces/{simple_name}_full.jsonl"
        if not os.path.exists(trace_file):
            return None
    with open(trace_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            if data.get("problem_id") == problem_id:
                return data
    return None

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    keyword = sys.argv[1]
    try:
        problem_id = int(sys.argv[2])
    except ValueError:
        print("Error: problem_id must be an integer")
        sys.exit(1)

    # 1. 根据关键词选择策略
    keyword_lower = keyword.lower()
    if "react" in keyword_lower:
        strategy = ReActStrategy()
        strategy_key = "ReAct"
    elif "plan" in keyword_lower:
        strategy = PlanExecuteStrategy()
        strategy_key = "PlanAndExecute"
    elif "self" in keyword_lower:
        strategy = SelfConsistencyStrategy()
        strategy_key = "SelfConsistency"
    else:
        print(f"Unknown strategy keyword: {keyword}. Use 'ReAct', 'Plan', or 'Self'.")
        sys.exit(1)

    print(f"Using strategy: {strategy.name}")
    print(f"Problem ID: {problem_id}")

    # 2. 加载数据集
    dataset = load_dataset()
    if problem_id >= len(dataset):
        print(f"Error: problem_id {problem_id} out of range (dataset size {len(dataset)})")
        sys.exit(1)

    problem_item = dataset[problem_id]
    question = problem_item["question"]
    ground_truth = problem_item["answer"]

    print(f"\nQuestion: {question[:200]}...")
    print(f"Ground truth answer: {ground_truth}")

    # 3. 重放（重新求解）
    print("\n--- Replaying ---")
    output = strategy.solve(question, problem_id=problem_id)
    new_answer = output.get("answer")
    print(f"Replayed answer: {new_answer}")

    # 4. 比较原 trace 中的答案（如果存在）
    original_trace = load_original_trace(strategy_key, problem_id)
    if original_trace:
        old_answer = original_trace.get("final_answer")
        print(f"Original answer (from trace): {old_answer}")
        if new_answer == old_answer:
            print("✅ Replay matches original trace.")
        else:
            print("⚠️ Replay differs from original trace.")
    else:
        print("(No original trace found for comparison)")

    # 5. 判断是否正确
    if new_answer is not None and abs(new_answer - ground_truth) < 1e-6:
        print("✅ The replayed answer is CORRECT.")
    else:
        print("❌ The replayed answer is WRONG.")
        print(f"   Expected: {ground_truth}, Got: {new_answer}")

    # 6. 可选：展示 trace 的前几步
    show_trace = input("\nShow first 2 events of trace? (y/n): ").strip().lower()
    if show_trace == 'y':
        for i, event in enumerate(output.get("trace", [])[:2]):
            print(f"Event {i+1}: {event.get('type')} -> {event.get('content', '')[:100]}...")

if __name__ == "__main__":
    main()