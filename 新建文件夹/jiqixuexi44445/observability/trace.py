import json
import time
from typing import Dict, Any, List
from datetime import datetime
import os

class TraceLogger:
    """将追踪事件写入 JSONL 文件"""

    def __init__(self, log_dir: str = "traces"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def log_event(self, strategy: str, problem_id: int, event: Dict[str, Any]):
        """记录单个事件"""
        event["strategy"] = strategy
        event["problem_id"] = problem_id
        event["timestamp"] = datetime.utcnow().isoformat()
        filename = os.path.join(self.log_dir, f"{strategy}_trace.jsonl")
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_full_trace(self, strategy: str, problem_id: int, trace: List[Dict], answer: Any):
        """记录完整 trace（批量写入）"""
        summary = {
            "strategy": strategy,
            "problem_id": problem_id,
            "final_answer": answer,
            "events": trace,
            "timestamp": datetime.utcnow().isoformat()
        }
        filename = os.path.join(self.log_dir, f"{strategy}_full.jsonl")
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")