# skills/base.py
"""
Skills 基类 - 所有自定义 Skills 都应该继承这个类
"""
import os
import re
import json
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel


class SkillMetadata(BaseModel):
    """Skill 元数据"""
    name: str
    description: str
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    author: Optional[str] = None
    version: Optional[str] = "1.0.0"


class SkillContext(BaseModel):
    """Skill 执行上下文"""
    user_message: str
    conversation_history: List[Dict[str, Any]]
    variables: Dict[str, Any] = {}


class SkillResult(BaseModel):
    """Skill 执行结果"""
    success: bool
    content: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseSkill(ABC):
    """所有 Skills 的基类"""
    
    def __init__(self, skill_dir: Path):
        self.skill_dir = skill_dir
        self._metadata = self._load_metadata()
        self._references = self._load_references()
    
    @abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult:
        """执行 Skill，必须由子类实现"""
        pass
    
    def _load_metadata(self) -> SkillMetadata:
        """从 SKILL.md 加载元数据"""
        skill_md_file = self.skill_dir / "SKILL.md"
        if not skill_md_file.exists():
            return SkillMetadata(
                name=self.skill_dir.name,
                description="No description available"
            )
        
        content = skill_md_file.read_text(encoding="utf-8")
        
        # 解析 frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            try:
                frontmatter = yaml.safe_load(frontmatter_text) or {}
                return SkillMetadata(**frontmatter)
            except Exception:
                pass
        
        return SkillMetadata(
            name=self.skill_dir.name,
            description="No description available"
        )
    
    def _load_references(self) -> Dict[str, str]:
        """加载 references 目录下的所有参考文档"""
        references_dir = self.skill_dir / "references"
        references = {}
        
        if not references_dir.exists():
            return references
        
        for ref_file in references_dir.glob("**/*.md"):
            relative_path = ref_file.relative_to(references_dir)
            references[str(relative_path)] = ref_file.read_text(encoding="utf-8")
        
        return references
    
    @property
    def metadata(self) -> SkillMetadata:
        """获取 Skill 元数据"""
        return self._metadata
    
    @property
    def references(self) -> Dict[str, str]:
        """获取参考文档"""
        return self._references
    
    @property
    def enabled(self) -> bool:
        """是否启用"""
        return True
    
    def get_full_content(self) -> str:
        """获取 SKILL.md 的完整内容"""
        skill_md_file = self.skill_dir / "SKILL.md"
        if skill_md_file.exists():
            return skill_md_file.read_text(encoding="utf-8")
        return ""


# 动态导入的 Python Skill 基类
class DynamicPythonSkill(BaseSkill):
    """从 SKILL.md 动态生成的 Python Skill"""
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """执行 Skill - 使用 AI 来理解和执行 SKILL.md 中的指令"""
        try:
            from openai import OpenAI
            from config import settings
            import httpx

            # 构建提示词
            prompt = f"""你是一个专业的 AI 助手，需要根据以下 Skill 指令来处理用户的请求。

## Skill 信息
名称: {self.metadata.name}
描述: {self.metadata.description}

## Skill 指令
{self.get_full_content()}

## 参考文档
{json.dumps(self.references, ensure_ascii=False, indent=2)}

## 用户请求
{context.user_message}

## 对话历史
{json.dumps(context.conversation_history[-5:], ensure_ascii=False, indent=2)}

请根据 Skill 指令处理用户请求，并返回适当的响应。不要提到 Skill，直接回答用户的问题。
"""

            # 调用 AI
            http_client = httpx.Client(timeout=30.0)
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                http_client=http_client
            )

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个执行 Skill 指令的 AI 助手。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            content = response.choices[0].message.content

            return SkillResult(
                success=True,
                content=content,
                metadata={"skill_name": self.metadata.name}
            )

        except Exception as e:
            return SkillResult(
                success=False,
                content="",
                error=str(e)
            )
