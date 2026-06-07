import openai
import time
import re
from typing import Dict, Any, List, Optional
from .base import Strategy
from config import MODEL_NAME, OPENAI_API_KEY, OPENAI_API_BASE, MAX_PLAN_EXECUTE_STEPS
from tools import Calculator

class PlanExecuteStrategy(Strategy):
    """Plan-and-Execute 策略：先规划，再逐步执行"""

    def __init__(self):
        self._name = "PlanAndExecute"
        self.calculator = Calculator()
        openai.api_key = OPENAI_API_KEY
        if OPENAI_API_BASE:
            openai.api_base = OPENAI_API_BASE

    @property
    def name(self) -> str:
        return self._name

    def _call_llm(self, prompt: str, temperature: float = 0.5, max_tokens: int = 800):
        start = time.time()
        try:
            response = openai.ChatCompletion.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            latency = int((time.time() - start) * 1000)
            content = response.choices[0].message.content
            usage = response.usage
            return content, usage.prompt_tokens, usage.completion_tokens, latency
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return f"[ERROR: {e}]", 0, 0, latency

    def _extract_final_number(self, text: str) -> Optional[float]:
        if not text or text.startswith("[ERROR"):
            return None
        match = re.search(r'####\s*([\d,\.]+)', text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
        match = re.search(r'Answer:\s*([\d,\.]+)', text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
        nums = re.findall(r'[\d,\.]+', text)
        for num_str in reversed(nums):
            try:
                return float(num_str.replace(',', ''))
            except:
                continue
        return None

    def solve(self, problem: str, problem_id: int = 0) -> Dict[str, Any]:
        trace = []

        # ---------- 步骤1: 生成计划 ----------
        planner_prompt = f"""你是一个计划制定者。对于下面的问题，请输出一个逐步解决的计划，每行一个步骤，编号。只输出计划，不要执行。

问题：{problem}

计划："""
        plan_text, pt, ct, latency = self._call_llm(planner_prompt, temperature=0.3)
        trace.append({
            "type": "plan",
            "content": plan_text,
            "token_usage": {"prompt": pt, "completion": ct, "total": pt + ct},
            "latency_ms": latency
        })

        # 解析步骤
        lines = plan_text.strip().split('\n')
        steps = []
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                clean = re.sub(r'^\d+\.\s*|^-\s*|^\*\s*', '', line)
                if clean:
                    steps.append(clean)
        if not steps:
            steps = [plan_text]
        trace.append({"type": "steps_parsed", "content": steps})

        # ---------- 步骤2: 逐步执行 ----------
        context = f"问题：{problem}\n计划：\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        step_results = []

        for idx, step_desc in enumerate(steps):
            executor_prompt = f"""{context}

当前正在执行步骤 {idx+1}/{len(steps)}：
{step_desc}

请执行这个步骤，进行必要的计算（可以心算或调用计算器），然后输出该步骤的结果。
如果步骤需要计算，请写出计算过程并给出数值结果。
最终输出该步骤的结果，格式为："步骤{idx+1}结果: <数值>"
"""
            step_out, pt, ct, latency = self._call_llm(executor_prompt, temperature=0.2)
            trace.append({
                "type": "step_execution",
                "step_index": idx,
                "step_text": step_desc,
                "output": step_out,
                "token_usage": {"prompt": pt, "completion": ct, "total": pt + ct},
                "latency_ms": latency
            })
            # 从步骤输出中提取数值（用于聚合）
            num = self._extract_final_number(step_out)
            step_results.append(num)
            context += f"\n步骤{idx+1}结果：{step_out}\n"

        # ---------- 步骤3: 汇总最终答案 ----------
        final_prompt = f"""根据以下各步骤的结果，给出最终答案。
问题：{problem}
步骤结果序列：{step_results}
最终答案（只输出数值）："""
        final_out, pt, ct, latency = self._call_llm(final_prompt, temperature=0.0, max_tokens=100)
        trace.append({
            "type": "final_aggregation",
            "output": final_out,
            "token_usage": {"prompt": pt, "completion": ct, "total": pt + ct},
            "latency_ms": latency
        })
        final_answer = self._extract_final_number(final_out)
        if final_answer is None:
            # 最后尝试从 step_results 中取最后一个非None值
            for val in reversed(step_results):
                if val is not None:
                    final_answer = val
                    break

        return {"answer": final_answer, "trace": trace, "steps": len(steps)}