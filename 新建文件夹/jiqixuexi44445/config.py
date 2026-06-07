import os
from dotenv import load_dotenv

load_dotenv()

# API 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("请设置 OPENAI_API_KEY 环境变量")

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", None)   # 可选，如 OpenRouter 或本地 Ollama
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

# 评估配置
EVAL_DATASET_SIZE = int(os.getenv("EVAL_DATASET_SIZE", "30"))
SELF_CONSISTENCY_SAMPLES = int(os.getenv("SELF_CONSISTENCY_SAMPLES", "5"))
MAX_REACT_STEPS = int(os.getenv("MAX_REACT_STEPS", "8"))
MAX_PLAN_EXECUTE_STEPS = int(os.getenv("MAX_PLAN_EXECUTE_STEPS", "10"))

# 成本估算（美元/1K tokens，GPT-3.5-turbo 近似）
COST_PER_1K_INPUT = float(os.getenv("COST_PER_1K_INPUT", "0.0005"))
COST_PER_1K_OUTPUT = float(os.getenv("COST_PER_1K_OUTPUT", "0.0015"))

# 随机种子
SEED = int(os.getenv("SEED", "42"))