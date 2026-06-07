import openai
import time
import re
from collections import Counter
from typing import Dict, Any, List, Optional
import concurrent.futures
from .base import Strategy
from config import MODEL_NAME, OPENAI_API_KEY, OPENAI_API_BASE, SELF_CONSISTENCY_SAMPLES

class SelfConsistencyStrategy(Strategy):
    """Self-Consistency: 多次采样 CoT，多数投票"""

    def __init__(self, num_samples: int = SELF_CONSISTENCY_SAMPLES):
        self.num_samples = num_samples
        self._name = f"SelfConsistency(N={num_samples})"
        openai.api_key = OPENAI_API_KEY
        if OPENAI_API_BASE:
            openai.api_base = OPENAI_API_BASE

    @property
    def name(self) -> str:
        return self._name

    def _call_llm(self, prompt: str, temperature: float = 0.7):
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

    def _extract_answer(self, text: str) -> Optional[float]:
        if not text or text.startswith("[ERROR"):
            return None
        # #### 数字
        match = re.search(r'####\s*([\d,\.]+)', text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
        # Answer: 数字
        match = re.search(r'Answer:\s*([\d,\.]+)', text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
        # 最后数字
        nums = re.findall(r'[\d,\.]+', text)
        for num_str in reversed(nums):
            try:
                return float(num_str.replace(',', ''))
            except:
                continue
        return None

    def _sample_once(self, problem: str, sample_id: int):
        prompt = f"""请一步步解决下面的数学问题，最后将答案放在 "####" 后。

问题：{problem}
逐步推理："""
        text, pt, ct, latency = self._call_llm(prompt, temperature=0.7)
        answer = self._extract_answer(text)
        return sample_id, text, answer, pt, ct, latency

    def solve(self, problem: str, problem_id: int = 0) -> Dict[str, Any]:
        traces = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_samples) as executor:
            futures = [executor.submit(self._sample_once, problem, i) for i in range(self.num_samples)]
            results = [f.result() for f in futures]

        answers = []
        for (sid, text, ans, pt, ct, latency) in results:
            answers.append(ans)
            traces.append({
                "type": "sample",
                "sample_id": sid,
                "output": text,
                "extracted_answer": ans,
                "token_usage": {"prompt": pt, "completion": ct, "total": pt + ct},
                "latency_ms": latency
            })

        valid_answers = [a for a in answers if a is not None]
        if not valid_answers:
            final_answer = None
        else:
            counter = Counter(valid_answers)
            final_answer = counter.most_common(1)[0][0]

        return {
            "answer": final_answer,
            "trace": traces,
            "samples": len(results),
            "vote_distribution": dict(Counter(valid_answers))
        }