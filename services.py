from openai import AsyncOpenAI
from config import settings


class ChatService:
    def __init__(self):
        self._client = None

    async def _get_client(self):
        """延迟初始化 OpenAI 客户端"""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                timeout=60.0
            )
        return self._client

    async def chat(self, messages: list, model: str = None) -> str:
        """
        发送聊天请求到 DeepSeek
        :param messages: 消息列表
        :param model: 模型名称
        :return: AI 响应
        """
        try:
            client = await self._get_client()

            response = await client.chat.completions.create(
                model=model or settings.DEFAULT_MODEL,
                messages=messages,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"Chat API 调用失败: {str(e)}")


chat_service = ChatService()
