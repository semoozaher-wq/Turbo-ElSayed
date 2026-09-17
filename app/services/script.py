# app/services/script.py

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.utils import logger
from app.config import Config
from app.services.llm_service import LLMService
from app.services.character_manager import CharacterManager

class MovieScenarioGenerator:
    """
    مولد سيناريو أفلام/مسلسلات باستخدام LLM، مع دعم ثبات الشخصيات وتوليد مشاهد فيديو.
    """
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.llm_service = LLMService(self.config)
        self.char_manager = CharacterManager(self.config)
        self.output_dir = self.config.get("app", "output_dir", "output")
        self.movie_mode = self.config.get_movie_mode()
        self.scene_duration = self.config.get_scene_duration()
        
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Movie Scenario Generator initialized (Movie Mode: {self.movie_mode})")

    def generate_script(self, topic: str, language: str = "ar", theme: str = "Drama") -> Dict[str, Any]:
        """
        توليد سيناريو فيلم/مسلسل كامل بناءً على الموضوع واللغة والنمط.
        :param topic: الموضوع العام للقصة
        :param language: لغة السيناريو
        :param theme: نمط القصة (دراما، كوميديا، إلخ)
        :return: ملف JSON يحتوي على السيناريو الكامل مع الشخصيات والمشاهد
        """
        logger.info(f"Generating movie scenario for: {topic} (Theme: {theme}, Language: {language})")
        
        # 1. استدعاء الـ LLM لتوليد القصة والشخصيات والمشاهد
        prompt = self._build_scenario_prompt(topic, language, theme)
        
        # استدعاء الـ LLM (نفترض وجود دالة generate_scenario في LLMService)
        scenario_data = self.llm_service.generate_scenario(prompt)
        
        # 2. معالجة البيانات وتثبيت الشخصيات
        scenario_data = self._fix_characters(scenario_data)
        
        # 3. حفظ الملف
        task_id = str(uuid.uuid4())
        output_file = os.path.join(self.output_dir, task_id, "scenario.json")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(scenario_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Scenario saved to {output_file}")
        return scenario_data

    def _build_scenario_prompt(self, topic: str, language: str, theme: str) -> str:
        """
        بناء الـ Prompt المطلوب من الـ LLM لتوليد سيناريو فيلم/مسلسل.
        """
        # جلب قائمة الشخصيات الثابتة من الملف
        characters_file = self.config.get_characters_file()
        if os.path.exists(characters_file):
            with open(characters_file, 'r', encoding='utf-8') as f:
                existing_chars = json.load(f)
            chars_info = json.dumps(existing_chars, ensure_ascii=False, indent=2)
            chars_instruction = f"شخصيات ثابتة: {chars_info}"
        else:
            chars_instruction = "لا توجد شخصيات سابقة، قم بإنشاء شخصيات جديدة."

        prompt = f"""
أنت مخرج سينمائي وناقد سينمائي محترف. المطلوب منك كتابة سيناريو فيلم/مسلسل كامل بناءً على التعليمات التالية:

الموضوع: {topic}
النمط: {theme}
اللغة: {language}

{chars_instruction}

الشروط الإلزامية:
1. **هيكلة السيناريو**: يجب أن يحتوي على:
   - عنوان الفيلم.
   - ملخص القصة (Logline).
   - قائمة الشخصيات الرئيسية مع وصف دقيق لكل شخصية (اسم، عمر، دورها، صفات نفسية).
   - تقسيم القصة إلى مشاهد (Scenes).
   
2. **تفاصيل كل مشهد**:
   - رقم المشهد.
   - نوع المكان (داخلي/خارجي) والوقت.
   - وصف بصري للمشهد (Visual Description) مناسب لتوليد فيديو (استخدم نموذج Kling/Midjourney).
   - الحوارات (Dialogue) لكل شخصية في المشهد.
   - ملاحظات الإخراج (Camera Angles، Effects).

3. **ثبات الشخصيات**:
   - حافظ على نفس وصف الشخصيات في كل المشاهد.
   - استخدم نفس أسماء الشخصيات وصفاتهم.
   - تأكد من أن تصرفات الشخصيات متسقة مع شخصياتهم.

4. **تنسيق الخرج**:
   - أخرج البيانات بصيغة JSON فقط (بدون نصوص إضافية).
   - الخرج المطلوب:
   ```json
   {
     "title": "عنوان الفيلم",
     "logline": "ملخص القصة",
     "characters": [...],
     "scenes": [
       {
         "id": 1,
         "location": "داخلي / ليل",
         "visual_prompt": "وصف بصري للمشهد...",
         "dialogues": [
           {"character": "اسم الشخصية", "line": "الحوار"}
         ]
       }
     ]
   }
