from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from services import chat_service
import os
import logging
import httpx
from openai import OpenAI
from config import settings
from skills.loader import skill_loader
from skills.matcher import skill_matcher
from skills.base import SkillContext, SkillResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# 配置代理（根据你的实际代理地址修改）
proxies = {
    "https://": "https://api.deepseek.com",
}

# 创建带代理的 httpx 客户端
http_client = httpx.Client(timeout=30.0)
client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    http_client=http_client)  



class Message(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    stream: bool = False
    enable_skills: bool = True


@router.get("/skills")
async def list_skills():
    """获取所有可用的 Skills"""
    skills = skill_loader.list_skills()
    return {
        "total": len(skills),
        "skills": [
            {
                "name": skill.name,
                "description": skill.description,
                "category": skill.category,
                "tags": skill.tags or [],
                "author": skill.author,
                "version": skill.version
            }
            for skill in skills
        ]
    }


@router.post("/skills/reload")
async def reload_skills():
    """重新加载所有 Skills"""
    skill_loader.reload()
    return {"message": "Skills reloaded successfully"}


@router.get("/skills/{skill_name}")
async def get_skill_detail(skill_name: str):
    """获取指定 Skill 的详细信息"""
    skill = skill_loader.get_skill(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    
    return {
        "metadata": skill.metadata.model_dump(),
        "references": list(skill.references.keys())
    }


@router.post("/")
async def chat(request: ChatRequest):
    """聊天接口 - 支持自动 Skills 调用"""
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    # 获取用户最新消息
    user_message = messages[-1]["content"] if messages else ""

    logger.info(f"收到聊天请求 - enable_skills={request.enable_skills}, user_message='{user_message}'")

    # 创建异步生成器
    async def generate():
        # 步骤1: 如果启用了 Skills，尝试匹配 Skill
        if request.enable_skills and user_message.strip():
            logger.info("开始匹配 Skill...")
            yield "🔍 分析请求...\n"

            matched = skill_matcher.match_skill(
                user_message,
                messages[:-1]
            )

            if matched:
                skill, confidence = matched
                logger.info(f"✅ 匹配到 Skill: {skill.metadata.name}, 置信度: {confidence:.2%}")
                yield f"✅ 找到合适的 Skill: {skill.metadata.name} (置信度: {confidence:.2%})\n\n"

                # 执行 Skill
                logger.info(f"📞 正在执行 Skill: {skill.metadata.name}")
                yield f"📞 正在执行 Skill: {skill.metadata.name}...\n"

                context = SkillContext(
                    user_message=user_message,
                    conversation_history=messages
                )

                result: SkillResult = await skill.execute(context)

                logger.info(f"Skill 执行结果 - success={result.success}, error={result.error}")

                if result.success:
                    logger.info(f"✅ Skill 执行成功, 内容长度: {len(result.content)}")
                    yield f"✅ 执行成功:\n\n{result.content}\n"
                else:
                    logger.error(f"❌ Skill 执行失败: {result.error}")
                    yield f"❌ 执行失败: {result.error}\n"

                # 更新对话历史
                messages.append({
                    "role": "assistant",
                    "content": f"使用了 {skill.metadata.name} Skill"
                })

                logger.info("Skill 执行完成，返回结果")
                return  # Skill 执行完成，不再调用普通聊天
            else:
                logger.info("未匹配到任何 Skill，继续普通聊天")
        else:
            if not request.enable_skills:
                logger.info("Skills 功能未启用，使用普通聊天")
            if not user_message.strip():
                logger.info("用户消息为空，跳过 Skill 匹配")

        # 步骤2: 普通 AI 聊天（没有匹配到 Skill 或未启用 Skills）
        logger.info("💭 开始普通 AI 聊天...")
        yield "💭 正在思考...\n"

        stream = client.chat.completions.create(
            model=request.model or "deepseek-chat",
            messages=messages,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

        logger.info("普通 AI 聊天完成")

    return StreamingResponse(generate(), media_type="text/plain")
