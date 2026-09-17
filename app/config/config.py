import os
import tomli
import tomli_w
from typing import Any, Dict, Optional
from app.utils import logger

# ... (بقية الكود الأصلي كما هو تماماً) ...
# لكن بما إنني مش عارف أقرأ ملفك الأصلي حرفياً، هكتبلك "النسخة المعدلة" كاملة بناءً على الكود المعروف للمشروع.

# =============================================================================
# START OF app/config/config.py (MODIFIED VERSION)
# =============================================================================

import os
import tomli
import tomli_w
from typing import Any, Dict, Optional
from app.utils import logger

class Config:
    def __init__(self, config_file: str = "config.toml"):
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        if not os.path.exists(self.config_file):
            logger.warning(f"Config file {self.config_file} not found. Creating default...")
            self._config = self._get_default_config()
            self.save_config()
            return

        try:
            with open(self.config_file, "rb") as f:
                self._config = tomli.load(f)
            logger.info(f"Config loaded from {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._config = self._get_default_config()

    def save_config(self) -> None:
        try:
            with open(self.config_file, "wb") as f:
                tomli_w.dump(self._config, f)
            logger.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "app": {
                "language": "zh",
                "output_dir": "output",
                "movie_mode": True,  # تفعيل وضع الفيلم الطويل
            },
            "llm": {
                "provider": "openai",
                "api_key": "",
                "model": "gpt-4o-mini",
                "base_url": "",
            },
            "voice": {
                "provider": "azure",
                "api_key": "",
                "region": "",
                "voice_id": "",
            },
            "subtitle": {
                "provider": "whisper",
                "model_size": "large-v3-turbo",
            },
            # ==========================================
            # إضافة أقسام جديدة لنظام "الأفلام والشخصيات الثابتة"
            # ==========================================
            "video_generation": {
                "image_provider": "midjourney",
                "image_api_key": "",
                "video_provider": "kling",
                "video_api_key": "",
                "character_reference_url": "",
                "scene_duration": 5,
            },
            "character_manager": {
                "characters_file": "assets/characters.json",
            }
        }

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self._config.get(section, {}).get(key, default)

    # --- دوال مساعدة للأقسام الجديدة (اللي الكود الجديد محتاجها) ---

    def get_image_provider(self) -> str:
        return self._config.get("video_generation", {}).get("image_provider", "midjourney")

    def get_image_api_key(self) -> str:
        return self._config.get("video_generation", {}).get("image_api_key", "")

    def get_video_provider(self) -> str:
        return self._config.get("video_generation", {}).get("video_provider", "kling")

    def get_video_api_key(self) -> str:
        return self._config.get("video_generation", {}).get("video_api_key", "")

    def get_character_reference_url(self) -> str:
        return self._config.get("video_generation", {}).get("character_reference_url", "")

    def get_scene_duration(self) -> int:
        return self._config.get("video_generation", {}).get("scene_duration", 5)

    def get_characters_file(self) -> str:
        return self._config.get("character_manager", {}).get("characters_file", "assets/characters.json")

    def get_movie_mode(self) -> bool:
        return self._config.get("app", {}).get("movie_mode", True)

# =============================================================================
# END OF app/config/config.py (MODIFIED VERSION)
# =============================================================================
