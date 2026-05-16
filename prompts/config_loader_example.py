import json
import os

class ConfigLoader:
    """配置加载器示例 - 用于加载 keywords.json"""
    
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = config_dir
        self.keywords = self._load_keywords()
    
    def _load_keywords(self):
        """加载关键词配置"""
        keywords_path = os.path.join(self.config_dir, "keywords.json")
        if os.path.exists(keywords_path):
            with open(keywords_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_chinese_keywords(self, category=None):
        """获取中文关键词"""
        if not self.keywords:
            return None
        if category:
            return self.keywords.get("chinese_keywords", {}).get(category)
        return self.keywords.get("chinese_keywords")
    
    def get_english_keywords(self, category=None):
        """获取英文关键词"""
        if not self.keywords:
            return None
        if category:
            return self.keywords.get("english_keywords", {}).get(category)
        return self.keywords.get("english_keywords")
    
    def get_transition_words(self):
        """获取过渡词"""
        if not self.keywords:
            return None
        return self.keywords.get("transition_words")


if __name__ == "__main__":
    loader = ConfigLoader()
    print("=" * 60)
    print("配置加载器示例")
    print("=" * 60)
    
    print(f"\n配置目录: {loader.config_dir}")
    print(f"关键词加载: {'成功' if loader.keywords else '失败'}")
    
    if loader.keywords:
        print(f"\n中文核心声明关键词: {len(loader.get_chinese_keywords('core_claim'))} 个")
        print(f"中文证据关键词: {len(loader.get_chinese_keywords('evidence'))} 个")
        print(f"中文蕴含关系词: {len(loader.get_chinese_keywords('entailment'))} 个")
        print(f"中文矛盾关系词: {len(loader.get_chinese_keywords('contradiction'))} 个")
        print(f"过渡词: {len(loader.get_transition_words())} 个")
        print("\n示例核心声明关键词:")
        print("  " + ", ".join(loader.get_chinese_keywords('core_claim')[:5]) + "...")
