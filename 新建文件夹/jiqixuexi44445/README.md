# jiqixuexi44445
# Agentic Reasoning Lab

## 概述
本项目实现了三种高级推理策略（ReAct、Plan-and-Execute、Self-Consistency），并在 GSM8K 数学题子集上进行严格评估，包括准确率、95% 置信区间、胜率矩阵、成本分析和追踪重放。

## 安装
```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY