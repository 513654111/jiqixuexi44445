from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class Strategy(ABC):
    """所有推理策略必须实现的接口"""
    
    @abstractmethod
    def solve(self, problem: str, problem_id: int = 0) -> Dict[str, Any]:
        """
        解决问题并返回结构化结果
        
        返回格式：
        {
            "answer": 最终答案 (数值或字符串),
            "trace": List[Dict]  # 每一步的详细日志
        }
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称，用于报告"""
        pass