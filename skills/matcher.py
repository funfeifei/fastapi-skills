# skills/matcher.py
"""
Skill 匹配器 - 根据用户请求自动选择合适的 Skill
"""
import re
from typing import List, Optional, Tuple, Dict
from pathlib import Path
from .loader import skill_loader
from .base import BaseSkill


class SkillMatcher:
    """Skill 匹配器"""
    
    def __init__(self):
        self.loader = skill_loader
    
    def match_skill(self, user_message: str, conversation_history: List[Dict] = None) -> Optional[Tuple[BaseSkill, float]]:
        """
        根据用户消息匹配最合适的 Skill
        
        Returns:
            (skill, confidence) - 匹配到的 Skill 和置信度 (0-1)
        """
        if conversation_history is None:
            conversation_history = []
        
        # 获取所有启用的 Skills
        skills = list(self.loader.get_all_skills().values())
        
        if not skills:
            return None
        
        # 方法1: 基于关键词匹配
        keyword_matches = self._match_by_keywords(user_message, skills)
        
        # 方法2: 基于语义匹配（使用 AI）
        semantic_matches = self._match_by_semantic(user_message, skills, conversation_history)
        
        # 综合两种方法的结果
        scores = {}
        for skill in skills:
            keyword_score = keyword_matches.get(skill, 0.0)
            semantic_score = semantic_matches.get(skill, 0.0)
            
            # 加权平均（关键词 40%，语义 60%）
            scores[skill] = keyword_score * 0.4 + semantic_score * 0.6
        
        # 找到得分最高的 Skill
        best_skill = max(scores.items(), key=lambda x: x[1])
        
        # 如果置信度太低，返回 None
        if best_skill[1] < 0.3:
            return None
        
        return best_skill
    
    def _match_by_keywords(self, user_message: str, skills: List[BaseSkill]) -> Dict[BaseSkill, float]:
        """基于关键词匹配"""
        scores = {}
        user_message_lower = user_message.lower()
        
        for skill in skills:
            score = 0.0
            
            # 检查 Skill 名称是否在消息中
            if skill.metadata.name.lower() in user_message_lower:
                score += 0.5
            
            # 从描述中提取关键词
            keywords = self._extract_keywords(skill.metadata.description)
            keywords.extend(self._extract_keywords(skill.get_full_content()))
            
            # 计算关键词匹配度
            matched_keywords = sum(1 for kw in keywords if kw in user_message_lower)
            if matched_keywords > 0:
                score += min(matched_keywords * 0.2, 0.5)
            
            scores[skill] = min(score, 1.0)
        
        return scores
    
    def _match_by_semantic(self, user_message: str, skills: List[BaseSkill], conversation_history: List[Dict]) -> Dict[BaseSkill, float]:
        """基于语义匹配（使用 AI）"""
        try:
            from openai import OpenAI
            from config import settings
            import httpx
            import json

            # 创建带超时的 httpx 客户端
            http_client = httpx.Client(timeout=30.0)

            # 构建提示词
            skill_descriptions = "\n".join([
                f"{i+1}. {skill.metadata.name}: {skill.metadata.description}"
                for i, skill in enumerate(skills)
            ])

            prompt = f"""你是 AI 助手，需要判断用户的请求应该使用哪个 Skill。

## 可用的 Skills
{skill_descriptions}

## 用户请求
"{user_message}"

## 任务
请分析用户请求，并判断它应该使用哪个 Skill。
- 如果用户请求明显匹配某个 Skill，返回该 Skill 的编号 (1-{len(skills)})
- 如果用户请求不匹配任何 Skill，返回 0
- 如果用户请求需要多个 Skill，返回最相关的一个

只返回数字，不要返回其他内容。"""

            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                http_client=http_client
            )
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是 Skill 匹配专家。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1  # 低温度以获得确定性结果
            )
            
            result = response.choices[0].message.content.strip()
            
            # 解析结果
            try:
                skill_index = int(result)
                if skill_index == 0:
                    return {skill: 0.0 for skill in skills}
                elif 1 <= skill_index <= len(skills):
                    matched_skill = skills[skill_index - 1]
                    # 给匹配的 Skill 高分，其他的低分
                    return {
                        skill: 0.9 if skill == matched_skill else 0.1
                        for skill in skills
                    }
            except ValueError:
                pass
            
            # 如果解析失败，返回默认分数
            return {skill: 0.0 for skill in skills}
            
        except Exception as e:
            print(f"Semantic matching error: {e}")
            return {skill: 0.0 for skill in skills}
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取：提取英文单词和常见中文术语
        keywords = []
        
        # 提取英文单词（长度 >= 3）
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords.extend(english_words)
        
        # 提取常见的技术术语和动作词
        action_words = [
            'review', 'search', 'find', 'install', 'get', 'use', 'create',
            'generate', 'execute', 'run', 'code', 'test', 'debug', 'fix',
            '分析', '搜索', '查找', '安装', '获取', '使用', '创建', '生成',
            '执行', '运行', '代码', '测试', '调试', '修复', '审查'
        ]
        
        for word in action_words:
            if word in text.lower():
                keywords.append(word)
        
        return list(set(keywords))
    
    def rank_skills(self, user_message: str, top_n: int = 3) -> List[Tuple[BaseSkill, float]]:
        """对 Skills 进行排序，返回前 N 个最相关的"""
        skills = list(self.loader.get_all_skills().values())
        
        if not skills:
            return []
        
        # 匹配所有 Skills
        keyword_scores = self._match_by_keywords(user_message, skills)
        semantic_scores = self._match_by_semantic(user_message, skills, [])
        
        # 计算综合得分
        ranked = []
        for skill in skills:
            score = keyword_scores[skill] * 0.4 + semantic_scores[skill] * 0.6
            ranked.append((skill, score))
        
        # 按得分降序排序
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked[:top_n]


# 全局 Skill Matcher 实例
skill_matcher = SkillMatcher()
