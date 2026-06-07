import openai
import time
import re
from typing import Dict, Any, List, Optional
from .base import Strategy
from config import MODEL_NAME, OPENAI_API_KEY, OPENAI_API_BASE, MAX_REACT_STEPS
from tools import Calculator

class ReActStrategy(Strategy):
    """ReAct (Reason + Act) 策略，带计算器工具"""

    def __init__(self):
        self._name = "ReAct"
        self.calculator = Calculator()
        openai.api_key = OPENAI_API_KEY
        if OPENAI_API_BASE:
            openai.api_base = OPENAI_API_BASE

    @property
    def name(self) -> str:
        return self._name

    def _call_llm(self, prompt: str, temperature: float = 0.7):
        """返回 (content, prompt_tokens, completion_tokens, latency_ms)"""
        start = time.time()
        try:
            response = openai.ChatCompletion.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=500
            )
            latency = int((time.time() - start) * 1000)
            content = response.choices[0].message.content
            usage = response.usage
            return content, usage.prompt_tokens, usage.completion_tokens, latency
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return f"[ERROR: {e}]", 0, 0, latency

    def _extract_final_number(self, text: str) -> Optional[float]:
        """从文本中安全提取最终数字"""
        if not text or text.startswith("[ERROR"):
            return None
        # 匹配 #### 数字（GSM8K 标准）
        match = re.search(r'####\s*([\d,\.]+)', text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
        # 匹配 Answer: 数字
        match = re.search(r'Answer:\s*([\d,\.]+)', text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
        # 最后出现的数字
        nums = re.findall(r'[\d,\.]+', text)
        for num_str in reversed(nums):
            try:
                return float(num_str.replace(',', ''))
            except:
                continue
        return None

    def solve(self, problem: str, problem_id: int = 0) -> Dict[str, Any]:
        trace = []
        system_prompt = f"""你是一个能使用工具的推理代理。你需要逐步推理，并在需要计算时使用计算器。

可用工具：
- Calculator: 计算数学表达式，例如 "2+3*4" -> 14.0

你必须严格按以下格式输出：
Thought: 你的推理过程
Action: 工具名称 (例如 Calculator)
Action Input: 输入表达式 (例如 2+3*4)
Observation: 工具返回的结果

... (可以重复 Thought/Action/Observation 多次)

当你知道最终答案时，输出：
Final Answer: 最终数值答案

现在开始解决问题：
{problem}
"""

        current_prompt = system_prompt
        steps = 0
        final_answer = None
        output = ""

        while steps < MAX_REACT_STEPS:
            steps += 1
            output, pt, ct, latency = self._call_llm(current_prompt)
            trace.append({
                "type": "llm_call",
                "content": output,
                "token_usage": {"prompt": pt, "completion": ct, "total": pt + ct},
                "latency_ms": latency,
                "step": steps
            })

            # 检查 Final Answer
            if "Final Answer:" in output:
                final_match = re.search(r'Final Answer:\s*(.*?)$', output, re.IGNORECASE | re.DOTALL)
                if final_match:
                    ans_text = final_match.group(1).strip()
                    final_answer = self._extract_final_number(ans_text)
                    if final_answer is not None:
                        break

            # 解析工具调用
            action_match = re.search(r'Action:\s*(\w+)', output, re.IGNORECASE)
            action_input_match = re.search(r'Action Input:\s*(.+)', output, re.IGNORECASE)
            if action_match and action_input_match:
                action = action_match.group(1).strip()
                action_input = action_input_match.group(1).strip()
                trace.append({"type": "action", "content": f"{action}({action_input})", "step": steps})
                if action.lower() == "calculator":
                    try:
                        result = self.calculator.evaluate(action_input)
                        observation = f"Observation: {result}"
                    except Exception as e:
                        observation = f"Observation: 计算错误 - {e}"
                else:
                    observation = f"Observation: 未知工具 '{action}'"
                trace.append({"type": "observation", "content": observation, "step": steps})
                current_prompt += f"\n{output}\n{observation}\n"
            else:
                # 没有工具调用，继续推理
                current_prompt += f"\n{output}\n"

        # 如果没有提取到最终答案，尝试从最后一次输出提取数字
        if final_answer is None:
            final_answer = self._extract_final_number(output)

        return {
            "answer": final_answer,
            "trace": trace,
            "steps": steps
        }