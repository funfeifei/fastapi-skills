---
name: calculator
description: 执行数学计算，支持加减乘除、括号等基本运算
category: utilities
tags: [math, calculation, tools]
---

# Calculator Skill

## When to Use
当用户需要执行数学计算时使用此 Skill。

## Examples
- "计算 2 + 3 * 4"
- "(10 - 5) / 2 等于多少？"
- "100 的平方根"

## How to Execute
1. 解析用户的数学表达式
2. 使用 Python 的 eval() 函数安全地计算结果
3. 返回计算结果

**注意**: 只允许基本的数学运算，禁止执行其他代码。
