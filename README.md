# FastAPI Skills

基于 FastAPI 和 DeepSeek AI 的智能聊天应用，支持可插拔的 Skills 功能。

## 功能特性

- 🚀 基于 FastAPI 的高性能后端
- 💬 集成 DeepSeek AI 模型
- 🎨 现代化的 Web UI 界面
- 📱 响应式设计，支持移动端
- 💾 支持多轮对话
- ⚡ 实时流式响应
- 🎯 **智能 Skills 系统** - 可扩展的 AI 能力插件
  - 📁 自动发现和加载 Skills
  - 🔍 智能匹配用户请求到合适的 Skill
  - 🔧 支持 Markdown 和 Python 两种实现方式
  - 🔄 热重载 Skills 无需重启服务
  - 📋 灵活的 Skill 元数据配置

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置你的 DeepSeek API Key:

```bash
cp .env.example .env
```

编辑 `.env` 文件:

```
OPENAI_API_KEY=your_actual_deepseek_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
```

### 3. 运行应用

```bash
python main.py
```

或者使用 uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问应用

打开浏览器访问: http://localhost:8000

## 项目结构

```
.
├── main.py                  # FastAPI 应用入口
├── config.py                # 配置管理
├── services.py              # 业务逻辑
├── api.py                   # API 路由
├── skills/
│   ├── base.py              # Skills 基类和数据模型
│   ├── loader.py            # Skills 自动加载器
│   ├── matcher.py           # Skills 智能匹配器
│   ├── calculator/           # 计算器 Skill
│   │   ├── SKILL.md         # Skill 说明文档
│   │   └── skill.py         # 自定义 Python 实现
│   ├── skill-lookup/        # Skill 查询
│   │   ├── SKILL.md
│   │   └── skill.yaml
│   └── frontend-code-review/  # 前端代码审查
│       ├── SKILL.md
│       ├── skill.yaml
│       └── references/
│           └── code-quality.md
├── static/
│   └── index.html           # Web UI 界面（支持 Skills）
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量示例
└── README.md               # 项目说明
```

## API 接口

### POST /api/chat/

发送聊天消息并获取 AI 回复（支持 Skills 自动调用）。

**请求体:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "计算 2 + 3 * 4"
    }
  ],
  "model": "deepseek-chat",
  "enable_skills": true
}
```

### GET /api/chat/skills

获取所有可用的 Skills 列表。

**响应:**

```json
{
  "total": 3,
  "skills": [
    {
      "name": "calculator",
      "description": "执行数学计算，支持加减乘除、括号等基本运算",
      "category": "utilities",
      "tags": ["math", "calculation", "tools"]
    }
  ]
}
```

### POST /api/chat/skills/reload

重新加载所有 Skills（热重载）。

### GET /api/chat/skills/{skill_name}

获取指定 Skill 的详细信息。

## 获取 DeepSeek API Key

1. 访问 DeepSeek 官网: https://platform.deepseek.com/
2. 注册/登录账号
3. 在控制台创建 API Key
4. 将 API Key 填入 `.env` 文件

## Skills 开发指南

### 创建新 Skill

1. 在 `skills/` 目录下创建新文件夹，例如 `my-skill/`

2. 创建 `SKILL.md` 文件：

```markdown
---
name: my-skill
description: 我的 Skill 描述
category: tools
tags: [tag1, tag2]
---

# My Skill

## When to Use
描述何时使用此 Skill。

## How to Execute
描述如何执行此 Skill。
```

3. （可选）创建 `skill.py` 实现自定义逻辑：

```python
from skills.base import BaseSkill, SkillContext, SkillResult

class MyCustomSkill(BaseSkill):
    async def execute(self, context: SkillContext) -> SkillResult:
        # 自定义执行逻辑
        return SkillResult(success=True, content="结果")
```

4. 重启服务或调用 API 热重载：
```bash
curl -X POST http://localhost:8000/api/chat/skills/reload
```

### Skill 匹配机制

系统使用混合匹配策略：
- **关键词匹配 (40%)**: 匹配 Skill 名称、描述中的关键词
- **语义匹配 (60%)**: 使用 AI 分析用户请求与 Skill 的语义相关性
- **置信度阈值**: 只有置信度 >= 30% 才会使用 Skill

## 技术栈

- **后端框架**: FastAPI
- **AI 模型**: DeepSeek (通过 OpenAI 兼容 API)
- **前端**: 原生 HTML/CSS/JavaScript
- **HTTP 服务器**: Uvicorn
- **Skills 系统**: 自动发现 + 动态加载 + 智能匹配

## 使用示例

### 启用 Skills 功能

在 Web UI 界面中：
1. 勾选顶部的 "启用 Skills" 复选框
2. 点击 "Skills" 按钮查看可用功能
3. 输入请求，系统会自动匹配并执行合适的 Skill

### 示例请求

- "计算 (10 - 5) / 2" → 使用 calculator Skill
- "查找代码审查的技能" → 使用 skill-lookup Skill
- "帮我分析这段代码" → 使用 frontend-code-review Skill

## 注意事项

- 确保网络可以访问 DeepSeek API
- 保护好你的 API Key，不要提交到版本控制系统
- 建议在生产环境中使用 HTTPS
- Skills 功能默认启用，可在界面中关闭
- 添加或修改 Skill 后，建议使用热重载功能更新

## License

MIT
