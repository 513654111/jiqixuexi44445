import openai
import time
import re
from typing import Dict, Any, List, Tuple
from config import MODEL_NAME, OPENAI_API_KEY, OPENAI_API_BASE

class LLMJudge:
    """使用 LLM 评估答案质量（用于自由形式答案）"""

    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        if OPENAI_API_BASE:
            openai.api_base = OPENAI_API_BASE

    def evaluate(self, question: str, ground_truth: str, agent_answer: str) -> Tuple[int, str]:
        """
        返回 (score, reasoning)
        score: 0-3
        """
        prompt = f"""你是一个严格但公正的评估者。评估以下答案。

问题: {question}
标准答案: {ground_truth}
学生答案: {agent_answer}

评分标准:
3 = 完全正确，且推理清晰
2 = 答案正确，但推理不完整或略有瑕疵
1 = 答案错误，但部分推理正确
0 = 完全错误或没有答案

请只输出JSON: {{"score": 0-3, "reasoning": "一句话理由"}}
"""
        try:
            response = openai.ChatCompletion.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=100
            )
            text = response.choices[0].message.content
            # 解析JSON
            import json
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return data.get("score", 0), data.get("reasoning", "")
            return 0, "解析失败"
        except Exception as e:
            return 0, f"Judge error: {e}"

    def sanity_check(self, examples: List[Dict]) -> float:
        """
        手动检查 judge 与人类的一致性
        examples: [{"question":..., "ground_truth":..., "agent_answer":..., "human_score": int}]
        返回一致性比例
        """
        correct = 0
        for ex in examples:
            pred_score, _ = self.evaluate(ex["question"], ex["ground_truth"], ex["agent_answer"])
            if pred_score == ex["human_score"]:
                correct += 1
        return correct / len(examples) if examples else 1.0