# skills/loader.py
"""
Skills 自动加载器 - 从 skills 目录自动发现和加载所有 Skills
"""
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Type, Optional
from .base import BaseSkill, SkillMetadata, DynamicPythonSkill


class SkillLoader:
    """Skill 自动加载器"""
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self._skills: Dict[str, BaseSkill] = {}
        self._load_all()
    
    def _load_all(self):
        """加载所有 Skills"""
        if not self.skills_dir.exists():
            print(f"Skills directory not found: {self.skills_dir}")
            return
        
        # 遍历 skills 目录下的所有子目录
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            # 跳过 __pycache__ 等目录
            if skill_dir.name.startswith("_") or skill_dir.name.startswith("."):
                continue
            
            # 检查是否有 SKILL.md 文件
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                print(f"Skipping {skill_dir.name}: No SKILL.md found")
                continue
            
            # 尝试加载 Python 实现文件
            py_file = skill_dir / "skill.py"
            if py_file.exists():
                # 加载自定义 Python Skill
                skill = self._load_python_skill(skill_dir, py_file)
            else:
                # 使用动态 AI 执行的 Skill
                skill = DynamicPythonSkill(skill_dir)
            
            if skill:
                self._skills[skill.metadata.name] = skill
                print(f"✅ Loaded skill: {skill.metadata.name}")
    
    def _load_python_skill(self, skill_dir: Path, py_file: Path) -> Optional[BaseSkill]:
        """加载自定义 Python Skill"""
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                f"skill_{skill_dir.name}",
                py_file
            )
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"skill_{skill_dir.name}"] = module
            spec.loader.exec_module(module)
            
            # 查找继承自 BaseSkill 的类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseSkill) and 
                    attr != BaseSkill and 
                    attr != DynamicPythonSkill):
                    # 实例化 Skill
                    return attr(skill_dir)
            
            return None
            
        except Exception as e:
            print(f"❌ Error loading Python skill from {skill_dir.name}: {e}")
            return None
    
    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取指定 Skill"""
        return self._skills.get(name)
    
    def get_all_skills(self) -> Dict[str, BaseSkill]:
        """获取所有 Skills"""
        return self._skills.copy()
    
    def list_skills(self) -> List[SkillMetadata]:
        """列出所有 Skills 的元数据"""
        return [skill.metadata for skill in self._skills.values()]
    
    def reload(self):
        """重新加载所有 Skills"""
        self._skills.clear()
        self._load_all()


# 全局 Skill Loader 实例
def get_skill_loader() -> SkillLoader:
    """获取全局 Skill Loader 实例"""
    from config import settings
    
    # 默认使用项目根目录下的 skills 目录
    base_dir = Path(__file__).parent.parent
    skills_dir = base_dir / "skills"
    
    return SkillLoader(skills_dir)


# 创建全局实例
skill_loader = get_skill_loader()
