import os
from typing import List, Dict
from app.config import config
from app.utils import logger
# من اللوجيك الحالي بتاع المشروع (تأكد من استيراد الدالة الصحيحة)
from app.services.llm import call_llm # مثال

class ScriptService:
    def __init__(self):
        self.language = config.get_language()

    def generate_screenplay(self, topic: str, characters: List[Dict] = None) -> List[Dict]:
        """
        توليد سيناريو فيلم مقسم لمشاهد
        """
        # بناء الـ Prompt
        prompt = f"""
        أنت كاتب سيناريو محترف.
        الموضوع: {topic}
        اللغة: {self.language}
        
        المطلوب:
        1. اكتب قصة قصيرة (فيلم أو مسلسل قصير) مقسمة لمشاهد (Scenes).
        2. كل مشهد يجب أن يحتوي على:
           - رقم المشهد (Scene #)
           - وصف دقيق للمشهد (الإضاءة، الخلفية، الحركة)
           - الشخصيات الموجودة في المشهد (من القائمة المرفقة فقط)
           - الحوار (Dialogues)
           - مدة المشهد المقترحة (ثواني)
        
        3. التزم بالمواصفات التالية:
           - الشخصيات ثابتة في كل مشهد (لا تغير ملامحها).
           - استخدم لغة درامية جذابة.
           - لا تخرج عن إطار القصة.
        
        قائمة الشخصيات المتاحة: {characters if characters else 'لا توجد'}
        
        صيغة الخروج: JSON Array من المشاهد.
        مثال:
        [
          {"scene_id": 1, "description": "قط برتقالي يرتدي سترة جلدية...", "dialogue": "...", "duration": 5},
          {"scene_id": 2, "description": "...", "dialogue": "...", "duration": 5}
        ]
        """

        try:
            # استدعاء LLM
            response = call_llm(prompt)
            # تحليل الرد وتحويله لقائمة مشاهد
            scenes = self._parse_llm_response(response)
            return scenes
        except Exception as e:
            logger.error(f"Error generating screenplay: {e}")
            return []

    def _parse_llm_response(self, response: str) -> List[Dict]:
        """
        تحويل رد الـ LLM (JSON) لقائمة مشاهد
        """
        import json
        try:
            # تنظيف الرد (أحياناً الـ LLM بيرجع نص + JSON)
            # هذا يحتاج تنظيف دقيق حسب الـ Response الفعلي
            data = json.loads(response) 
            return data
        except:
            return []

# ملاحظة: تأكد من استيراد الدالة الصحيحة بتاعتك