from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class Strategy(ABC):
    """所有推理策略的统一接口"""

    @abstractmethod
    def solve(self, problem: str, problem_id: int = 0) -> Dict[str, Any]:
        """
        解决问题

        Args:
            problem: 问题文本
            problem_id: 问题ID（用于追踪）

        Returns:
            {
                "answer": 最终答案（数值或字符串），
                "trace": List[Dict]，每个事件包含：
                    {
                        "type": "thought" / "action" / "observation" / "llm_call",
                        "content": str,
                        "token_usage": {"prompt": int, "completion": int, "total": int},
                        "latency_ms": int
                    }
            }
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass