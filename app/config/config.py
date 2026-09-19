"""Standalone application configuration.

The module exposes configuration sections as dictionaries so existing modules can
use ``from app.config import config`` without depending on another project.
Secrets should be supplied through config.toml or environment variables and are
never logged by this module.
"""

from __future__ import annotations

import os
import shutil
import socket
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 compatibility
    import tomli as tomllib

try:
    import toml
except ModuleNotFoundError:  # pragma: no cover - minimal installations
    toml = None

from loguru import logger


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = ROOT_DIR / "config.toml"
EXAMPLE_CONFIG_FILE = ROOT_DIR / "config.example.toml"

_config_save_lock = threading.RLock()
_runtime_config_lock = threading.RLock()
_pending_config_lock = threading.RLock()
_pending_config_updates: dict[tuple[int, str], tuple[dict[str, Any], str, Any]] = {}
_pending_config_flush_scheduled = False
_MISSING = object()


class SynchronizedSection(dict):
    """Dictionary section that persists changes through the module save helper."""

    def __setitem__(self, key: str, value: Any) -> None:
        with _config_save_lock:
            super().__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        with _config_save_lock:
            super().__delitem__(key)

    def update(self, *args: Any, **kwargs: Any) -> None:
        changes = dict(*args, **kwargs)
        with _config_save_lock:
            super().update(changes)


# Backward-compatible private name used by older tests.
_SynchronizedConfig = SynchronizedSection


def _defaults() -> dict[str, Any]:
    return {
        "log_level": "INFO",
        "listen_host": "0.0.0.0",
        "listen_port": 8501,
        "reload_debug": False,
        "project_name": "Turbo ElSayed",
        "project_version": "1.0.0",
        "project_description": "Standalone Arabic movie and scenario generator",
        "app": {
            "name": "Turbo ElSayed",
            "language": "ar",
            "output_dir": "output",
            "movie_mode": True,
            "api_key": "",
            "video_source": "local",
            "script_generation_backend": "local",
            "llm_provider": "gemini",
        },
        "scenario": {
            "provider": "gemini",
            "language": "ar",
            "model": "gemini-2.5-flash",
            "base_url": "",
            "api_key": "",
            "temperature": 0.7,
            "scene_count": 8,
            "scene_duration": 5,
            "output_dir": "output/scenarios",
            "characters_file": "characters.json",
        },
        "llm": {
            "provider": "gemini",
            "api_key": "",
            "base_url": "",
            "model": "gemini-2.5-flash",
        },
        "character_manager": {
            "characters_file": "characters.json",
            "character_strength": 0.8,
        },
        "video_generation": {
            "image_provider": "none",
            "image_api_key": "",
            "character_reference_url": "",
            "video_provider": "none",
            "video_api_key": "",
            "scene_duration": 5,
            "aspect_ratio": "16:9",
            "resolution": "1080p",
        },
        "subtitle": {"provider": "none", "model_size": "large-v3-turbo", "language": "ar"},
        "voice": {"provider": "none", "api_key": "", "region": "", "voice_id": ""},
        "proxy": {"enabled": False, "http": "", "https": "", "verify_tls": True},
        "ui": {"language": "ar", "hide_config": False, "show_logs": True, "hide_log": False},
        "storage": {
            "output_dir": "output",
            "scenarios_dir": "output/scenarios",
            "logs_dir": "output/logs",
            "temporary_dir": "output/tmp",
        },
    }


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _load_file() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        if EXAMPLE_CONFIG_FILE.exists():
            shutil.copyfile(EXAMPLE_CONFIG_FILE, CONFIG_FILE)
        else:
            return _defaults()
    try:
        with CONFIG_FILE.open("rb") as handle:
            loaded = tomllib.load(handle)
    except (OSError, ValueError, UnicodeError) as exc:
        logger.warning("Unable to load config.toml: {}", exc)
        loaded = {}
    return _deep_merge(_defaults(), loaded)


def _write_toml(data: Mapping[str, Any]) -> str:
    if toml is not None:
        return toml.dumps(dict(data))
    lines: list[str] = []
    scalar_keys = [key for key, value in data.items() if not isinstance(value, Mapping)]
    for key in scalar_keys:
        lines.append(f"{key} = {repr(data[key])}")
    for section, values in data.items():
        if not isinstance(values, Mapping):
            continue
        lines.append("")
        lines.append(f"[{section}]")
        for key, value in values.items():
            if isinstance(value, bool):
                encoded = "true" if value else "false"
            elif isinstance(value, str):
                encoded = '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
            else:
                encoded = repr(value)
            lines.append(f"{key} = {encoded}")
    return "\n".join(lines) + "\n"


def _section(name: str) -> SynchronizedSection:
    value = _cfg.get(name, {})
    return SynchronizedSection(value if isinstance(value, Mapping) else {})


_cfg = _load_file()
app = _section("app")
scenario = _section("scenario")
llm = _section("llm")
character_manager = _section("character_manager")
video_generation = _section("video_generation")
whisper = _section("whisper")
subtitle = _section("subtitle")
voice = _section("voice")
proxy = _section("proxy")
ui = _section("ui")
azure = _section("azure")
siliconflow = _section("siliconflow")
minimax_tts = _section("minimax_tts")
elevenlabs = _section("elevenlabs")
chatterbox = _section("chatterbox")
kokoro = _section("kokoro")
fish_audio = _section("fish_audio")
voxcpm = _section("voxcpm")
storage = _section("storage")

hostname = socket.gethostname()
log_level = str(_cfg.get("log_level", "INFO")).upper()
listen_host = str(_cfg.get("listen_host", "0.0.0.0"))
listen_port = int(_cfg.get("listen_port", 8501))
project_name = str(_cfg.get("project_name", "Turbo ElSayed"))
project_version = str(_cfg.get("project_version", "1.0.0"))
project_description = str(_cfg.get("project_description", "Standalone Arabic movie and scenario generator"))
reload_debug = bool(_cfg.get("reload_debug", False))


def _sync_sections() -> None:
    for name in (
        "app", "scenario", "llm", "character_manager", "video_generation",
        "subtitle", "voice", "proxy", "ui", "azure", "siliconflow",
        "minimax_tts", "elevenlabs", "chatterbox", "kokoro", "fish_audio",
        "voxcpm", "storage",
    ):
        _cfg[name] = dict(globals().get(name, {}))


def save_config() -> None:
    """Persist current settings atomically to config.toml."""
    with _config_save_lock:
        _sync_sections()
        temporary = CONFIG_FILE.with_suffix(".toml.tmp")
        temporary.write_text(_write_toml(_cfg), encoding="utf-8")
        os.replace(temporary, CONFIG_FILE)


def try_save_config() -> bool:
    try:
        save_config()
        return True
    except OSError as exc:
        logger.error("Unable to save configuration: {}", exc)
        return False


def snapshot_config_with_pending(config_section: Mapping[str, Any]) -> dict[str, Any]:
    return dict(config_section)


def update_config_nonblocking(config_section: dict[str, Any], key: str, value: Any) -> bool:
    """Update a setting immediately unless a runtime generation is in progress."""
    if _runtime_config_lock.acquire(blocking=False):
        try:
            config_section[key] = value
            return True
        finally:
            _runtime_config_lock.release()
    with _pending_config_lock:
        _pending_config_updates[(id(config_section), key)] = (config_section, key, value)
    return False


def delete_config_nonblocking(config_section: dict[str, Any], key: str) -> bool:
    if _runtime_config_lock.acquire(blocking=False):
        try:
            config_section.pop(key, None)
            return True
        finally:
            _runtime_config_lock.release()
    with _pending_config_lock:
        _pending_config_updates[(id(config_section), key)] = (config_section, key, _MISSING)
    return False


@contextmanager
def runtime_config_lock() -> Iterator[None]:
    with _runtime_config_lock:
        yield
    _flush_pending_config_updates()


@contextmanager
def try_runtime_config_lock() -> Iterator[bool]:
    acquired = _runtime_config_lock.acquire(blocking=False)
    try:
        yield acquired
    finally:
        if acquired:
            _runtime_config_lock.release()
            _flush_pending_config_updates()


def _flush_pending_config_updates() -> None:
    with _pending_config_lock:
        updates = list(_pending_config_updates.values())
        _pending_config_updates.clear()
    for section, key, value in updates:
        if value is _MISSING:
            section.pop(key, None)
        else:
            section[key] = value


def is_running_in_container() -> bool:
    return Path("/.dockerenv").exists() or os.getenv("container", "").lower() in {"docker", "podman"}


def get_container_default_gateway_ip() -> str:
    return os.getenv("HOST_GATEWAY", "host.docker.internal")


def get_default_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")


# Compatibility helpers used by the standalone scenario service.
def get_image_provider() -> str:
    return str(video_generation.get("image_provider", "none"))


def get_image_api_key() -> str:
    return str(video_generation.get("image_api_key", ""))


def get_video_provider() -> str:
    return str(video_generation.get("video_provider", "none"))


def get_video_api_key() -> str:
    return str(video_generation.get("video_api_key", ""))


def get_character_reference_url() -> str:
    return str(video_generation.get("character_reference_url", ""))


def get_scene_duration() -> int:
    try:
        return max(1, int(video_generation.get("scene_duration", 5)))
    except (TypeError, ValueError):
        return 5


def get_characters_file() -> str:
    return str(character_manager.get("characters_file", "characters.json"))


def get_movie_mode() -> bool:
    return bool(app.get("movie_mode", True))


# Class facade retained for callers that prefer constructing an isolated config.
class Config:
    """Small isolated view over a TOML configuration mapping."""

    def __init__(self, config_file: str | os.PathLike[str] = CONFIG_FILE) -> None:
        self.config_file = Path(config_file)
        self._config: dict[str, Any] = _load_file() if self.config_file == CONFIG_FILE else self._load_local()

    def _load_local(self) -> dict[str, Any]:
        if not self.config_file.exists():
            return _defaults()
        with self.config_file.open("rb") as handle:
            return _deep_merge(_defaults(), tomllib.load(handle))

    @property
    def log_level(self) -> str:
        return str(self._config.get("log_level", "INFO")).upper()

    def get(self, section: str, key: str, default: Any = None) -> Any:
        value = self._config.get(section, {})
        return value.get(key, default) if isinstance(value, Mapping) else default

    def get_image_provider(self) -> str:
        return str(self.get("video_generation", "image_provider", "none"))

    def get_image_api_key(self) -> str:
        return str(self.get("video_generation", "image_api_key", ""))

    def get_video_provider(self) -> str:
        return str(self.get("video_generation", "video_provider", "none"))

    def get_video_api_key(self) -> str:
        return str(self.get("video_generation", "video_api_key", ""))

    def get_character_reference_url(self) -> str:
        return str(self.get("video_generation", "character_reference_url", ""))

    def get_scene_duration(self) -> int:
        try:
            return max(1, int(self.get("video_generation", "scene_duration", 5)))
        except (TypeError, ValueError):
            return 5

    def get_characters_file(self) -> str:
        return str(self.get("character_manager", "characters_file", "characters.json"))

    def get_movie_mode(self) -> bool:
        return bool(self.get("app", "movie_mode", True))


__all__ = [
    "Config", "app", "scenario", "llm", "character_manager", "video_generation",
    "subtitle", "voice", "proxy", "ui", "azure", "siliconflow", "minimax_tts",
    "elevenlabs", "chatterbox", "kokoro", "fish_audio", "voxcpm", "storage",
    "log_level", "listen_host", "listen_port", "project_name", "project_version",
    "project_description", "reload_debug", "save_config", "try_save_config",
    "snapshot_config_with_pending", "update_config_nonblocking", "delete_config_nonblocking",
    "runtime_config_lock", "try_runtime_config_lock", "is_running_in_container",
    "get_container_default_gateway_ip", "get_default_ollama_base_url",
]
