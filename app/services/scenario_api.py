"""Application-facing API for standalone scenario generation.

This adapter keeps the Web UI and HTTP layers independent from provider details.
It uses the local ``MovieScenarioGenerator`` and returns JSON-serializable data.
"""

from __future__ import annotations

from typing import Any, Mapping

from app.config import config
from app.services.script import MovieScenarioGenerator, ScenarioGenerationError


_generator = MovieScenarioGenerator(config=config)


def get_generator() -> MovieScenarioGenerator:
    """Return the shared scenario generator instance."""
    return _generator


def generate_scenario(
    topic: str,
    *,
    language: str = "ar",
    theme: str = "Drama",
    scene_count: int = 8,
    save: bool = True,
) -> dict[str, Any]:
    """Generate and optionally save a structured scenario."""
    return get_generator().generate_script(
        topic=topic,
        language=language,
        theme=theme,
        scene_count=scene_count,
        save=save,
    )


def generate_scenario_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Generate a scenario from a request-like mapping.

    Accepted keys are ``topic``/``video_subject``, ``language``/``video_language``,
    ``theme``, ``scene_count`` and ``save``. Unknown keys are ignored.
    """
    topic = payload.get("topic") or payload.get("video_subject") or ""
    language = payload.get("language") or payload.get("video_language") or "ar"
    theme = payload.get("theme") or "Drama"
    scene_count = payload.get("scene_count", 8)
    save = payload.get("save", True)
    return generate_scenario(
        str(topic),
        language=str(language),
        theme=str(theme),
        scene_count=int(scene_count),
        save=bool(save),
    )


__all__ = [
    "ScenarioGenerationError",
    "generate_scenario",
    "generate_scenario_from_payload",
    "get_generator",
]
