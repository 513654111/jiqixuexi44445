import json
import random
from typing import List, Dict, Any

def load_gsm8k_subset(file_path: str, size: int = 30, seed: int = 42) -> List[Dict[str, Any]]:
    """
    从 GSM8K test.jsonl 加载子集
    若文件不存在，返回模拟数据
    """
    random.seed(seed)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        data = []
        for line in lines:
            item = json.loads(line)
            # GSM8K 格式: {"question": "...", "answer": "#### 18"}
            question = item.get("question", "")
            answer_text = item.get("answer", "")
            # 提取答案数字
            import re
            match = re.search(r'####\s*([\d,\.]+)', answer_text)
            if match:
                answer = float(match.group(1).replace(',', ''))
            else:
                continue
            data.append({"question": question, "answer": answer})
        if len(data) > size:
            data = random.sample(data, size)
        return data
    except FileNotFoundError:
        # 返回模拟数据
        mock_data = [
            {"question": "Janet's ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four. She sells the remainder at the farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers' market?", "answer": 18.0},
            {"question": "A robe takes 2 bolts of blue fiber and half that much white fiber. How many bolts in total does it take?", "answer": 3.0},
            {"question": "Out of 180 students in a school, 50% are girls. If the number of boys is 60, how many girls are there?", "answer": 90.0},
            {"question": "If 6 cans of soda cost $2.70, how much would 10 cans cost?", "answer": 4.5},
            {"question": "Leo has 5 boxes of crayons with 8 crayons in each box. He gives away 12 crayons. How many crayons does Leo have left?", "answer": 28.0},
        ]
        return mock_data[:size]