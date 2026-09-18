"""Standalone movie and episodic scenario generation service.

This module intentionally has no dependency on MoneyPrinterTurbo-specific modules.
It can use any OpenAI-compatible API when a client is supplied or when the
OPENAI_API_KEY environment variable is configured.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Mapping, Protocol

from loguru import logger


class ChatClient(Protocol):
    """Minimal protocol implemented by OpenAI-compatible chat clients."""

    @property
    def chat(self) -> Any: ...


class ScenarioGenerationError(RuntimeError):
    """Raised when a scenario cannot be generated or parsed."""


class MovieScenarioGenerator:
    """Generate structured movie scenarios and preserve character continuity.

    The service is deliberately self-contained. Configuration may be supplied
    as a mapping, a plain object with attributes, or omitted entirely. A client
    can be injected for tests or for any OpenAI-compatible provider.
    """

    def __init__(
        self,
        config: Any = None,
        client: ChatClient | None = None,
        output_dir: str | os.PathLike[str] | None = None,
        characters_file: str | os.PathLike[str] | None = None,
        model: str | None = None,
    ) -> None:
        self.config = config
        self.client = client
        self.model = model or self._setting(
            "model",
            default=os.getenv("SCENARIO_MODEL", "gpt-4o-mini"),
        )
        self.output_dir = Path(
            output_dir
            or self._setting("output_dir", default=os.getenv("SCENARIO_OUTPUT_DIR", "output"))
        )
        self.characters_file = Path(
            characters_file
            or self._setting(
                "characters_file",
                default=os.getenv("CHARACTERS_FILE", "characters.json"),
            )
        )
        self.scene_duration = self._positive_int(
            self._setting("scene_duration", default=5), default=5
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_script(
        self,
        topic: str,
        language: str = "ar",
        theme: str = "Drama",
        scene_count: int = 8,
        save: bool = True,
    ) -> dict[str, Any]:
        """Generate a complete scenario and optionally save it as JSON."""
        topic = str(topic or "").strip()
        language = str(language or "ar").strip()
        theme = str(theme or "Drama").strip()
        if not topic:
            raise ValueError("topic must not be empty")
        scene_count = max(1, min(self._positive_int(scene_count, 8), 50))

        fixed_characters = self.load_characters()
        prompt = self.build_prompt(
            topic=topic,
            language=language,
            theme=theme,
            scene_count=scene_count,
            fixed_characters=fixed_characters,
        )
        raw_response = self._request(prompt)
        scenario = self._parse_json_response(raw_response)
        scenario = self.normalize_scenario(
            scenario,
            topic=topic,
            language=language,
            theme=theme,
            scene_count=scene_count,
            fixed_characters=fixed_characters,
        )

        if save:
            output_file = self.save_scenario(scenario)
            scenario["output_file"] = str(output_file)
        return scenario

    def build_prompt(
        self,
        topic: str,
        language: str,
        theme: str,
        scene_count: int,
        fixed_characters: list[dict[str, Any]],
    ) -> str:
        fixed_json = json.dumps(fixed_characters, ensure_ascii=False, indent=2)
        return f"""You are an experienced screenwriter and visual storyteller.
Create a complete fictional scenario based on the following brief.

Topic: {topic}
Language: {language}
Genre or theme: {theme}
Number of scenes: {scene_count}
Duration per scene: {self.scene_duration} seconds
Existing fixed characters (reuse them when present):
{fixed_json}

Return ONLY valid JSON. Do not wrap it in Markdown fences and do not add commentary.
Use exactly this structure:
{{
  "title": "string",
  "logline": "string",
  "language": "{language}",
  "theme": "{theme}",
  "characters": [
    {{
      "id": "string",
      "name": "string",
      "age": "string",
      "role": "string",
      "personality": "string",
      "appearance": "string",
      "continuity_notes": "string"
    }}
  ],
  "scenes": [
    {{
      "id": 1,
      "duration": {self.scene_duration},
      "location": "string",
      "time": "string",
      "visual_prompt": "string",
      "action": "string",
      "dialogues": [
        {{"character": "string", "line": "string"}}
      ],
      "camera": "string",
      "sound": "string"
    }}
  ]
}}

Keep character names, appearance, personality, and continuity notes consistent in every scene.
""".strip()

    def load_characters(self) -> list[dict[str, Any]]:
        """Load reusable characters; a missing file is treated as an empty list."""
        if not self.characters_file.exists():
            return []
        try:
            data = json.loads(self.characters_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Unable to read characters file {}: {}", self.characters_file, exc)
            return []
        if isinstance(data, dict):
            data = data.get("characters", [])
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def save_scenario(self, scenario: Mapping[str, Any]) -> Path:
        """Save a scenario in a unique directory and return its JSON path."""
        scenario_id = str(uuid.uuid4())
        scenario_dir = self.output_dir / scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        output_file = scenario_dir / "scenario.json"
        output_file.write_text(
            json.dumps(dict(scenario), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Scenario saved to {}", output_file)
        return output_file

    def normalize_scenario(
        self,
        scenario: Mapping[str, Any],
        *,
        topic: str,
        language: str,
        theme: str,
        scene_count: int,
        fixed_characters: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Fill safe defaults and enforce character continuity in all scenes."""
        result = dict(scenario)
        result["title"] = str(result.get("title") or topic).strip()
        result["logline"] = str(result.get("logline") or topic).strip()
        result["language"] = str(result.get("language") or language)
        result["theme"] = str(result.get("theme") or theme)

        characters = result.get("characters")
        if not isinstance(characters, list):
            characters = []
        characters = [self._normalize_character(item, index) for index, item in enumerate(characters)]
        if fixed_characters:
            characters = self._merge_characters(fixed_characters, characters)
        result["characters"] = characters

        scenes = result.get("scenes")
        if not isinstance(scenes, list):
            scenes = []
        normalized_scenes = []
        for index, scene in enumerate(scenes[:scene_count], start=1):
            if not isinstance(scene, dict):
                scene = {}
            item = dict(scene)
            item["id"] = index
            item["duration"] = self._positive_int(item.get("duration"), self.scene_duration)
            item["location"] = str(item.get("location") or "unspecified")
            item["time"] = str(item.get("time") or "day")
            item["visual_prompt"] = str(item.get("visual_prompt") or item.get("action") or "")
            item["action"] = str(item.get("action") or "")
            item["camera"] = str(item.get("camera") or "cinematic")
            item["sound"] = str(item.get("sound") or "ambient sound")
            dialogues = item.get("dialogues")
            item["dialogues"] = self._normalize_dialogues(dialogues)
            normalized_scenes.append(item)
        result["scenes"] = normalized_scenes
        return result

    def _request(self, prompt: str) -> str:
        client = self.client or self._create_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Return only valid JSON. Do not use Markdown fences.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        if not content or not str(content).strip():
            raise ScenarioGenerationError("The model returned an empty response")
        return str(content)

    def _create_client(self) -> ChatClient:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ScenarioGenerationError(
                "Install the 'openai' package or inject an OpenAI-compatible client"
            ) from exc
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ScenarioGenerationError(
                "OPENAI_API_KEY is not configured and no client was injected"
            )
        base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
        return OpenAI(api_key=api_key, base_url=base_url)

    @staticmethod
    def _parse_json_response(text: str) -> dict[str, Any]:
        cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
        try:
            value = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise ScenarioGenerationError("The model response does not contain valid JSON")
            try:
                value = json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise ScenarioGenerationError("The model returned malformed JSON") from exc
        if not isinstance(value, dict):
            raise ScenarioGenerationError("The model JSON response must be an object")
        return value

    def _setting(self, key: str, default: Any = None) -> Any:
        if self.config is None:
            return default
        if isinstance(self.config, Mapping):
            for section in ("scenario", "app", "video_generation", "character_manager"):
                section_data = self.config.get(section)
                if isinstance(section_data, Mapping) and key in section_data:
                    return section_data[key]
            return self.config.get(key, default)
        value = getattr(self.config, key, None)
        if value is not None:
            return value
        data = getattr(self.config, "_config", None)
        if isinstance(data, Mapping):
            return MovieScenarioGenerator(data)._setting(key, default)
        return default

    @staticmethod
    def _positive_int(value: Any, default: int) -> int:
        try:
            result = int(value)
        except (TypeError, ValueError):
            return default
        return result if result > 0 else default

    @staticmethod
    def _normalize_character(item: Any, index: int) -> dict[str, Any]:
        item = item if isinstance(item, Mapping) else {}
        name = str(item.get("name") or f"Character {index + 1}")
        return {
            "id": str(item.get("id") or re.sub(r"\W+", "-", name.lower()).strip("-") or f"character-{index + 1}"),
            "name": name,
            "age": str(item.get("age") or "adult"),
            "role": str(item.get("role") or "supporting character"),
            "personality": str(item.get("personality") or "consistent and believable"),
            "appearance": str(item.get("appearance") or "as established in the first scene"),
            "continuity_notes": str(item.get("continuity_notes") or "Keep appearance and personality unchanged."),
        }

    @staticmethod
    def _merge_characters(
        fixed: list[dict[str, Any]], generated: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        merged = [MovieScenarioGenerator._normalize_character(item, i) for i, item in enumerate(fixed)]
        existing = {item["name"].casefold() for item in merged}
        for item in generated:
            if item["name"].casefold() not in existing:
                merged.append(item)
                existing.add(item["name"].casefold())
        return merged

    @staticmethod
    def _normalize_dialogues(value: Any) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        result = []
        for item in value:
            if isinstance(item, Mapping):
                result.append(
                    {
                        "character": str(item.get("character") or "Narrator"),
                        "line": str(item.get("line") or ""),
                    }
                )
        return result


__all__ = ["MovieScenarioGenerator", "ScenarioGenerationError"]
