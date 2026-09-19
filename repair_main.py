from __future__ import annotations

import re
from pathlib import Path

path = Path(__file__).resolve().parent / "webui" / "Main.py"
if not path.exists():
    raise SystemExit(f"Main.py not found: {path}")

text = path.read_text(encoding="utf-8")

# Replace any broken or old streamlit-tour import block, including a dangling try:.
text, import_count = re.subn(
    r"(?ms)^try:\s*\n(?:\s+from\s+streamlit_tour\s+import\s+Tour.*\n)?(?:\s+except\s+ImportError[^\n]*:\s*\n\s+Tour\s*=\s*None\s*\n)?",
    "Tour = None\n",
    text,
    count=1,
)
if import_count == 0:
    text = re.sub(r"(?m)^\s*from\s+streamlit_tour\s+import\s+Tour\s*$\n?", "Tour = None\n", text)

# Replace the complete onboarding function up to the next top-level function.
new_function = '''def render_onboarding_tour():
    """Optional onboarding tour disabled; streamlit-tour is not required."""
    return None


'''
text, function_count = re.subn(
    r"(?ms)^def render_onboarding_tour\(\):\n.*?(?=^def _render_generation_logs\()",
    new_function,
    text,
    count=1,
)
if function_count == 0:
    raise SystemExit("Could not locate render_onboarding_tour in Main.py")

path.write_text(text, encoding="utf-8")
print(f"Repaired {path}")
print("Removed broken tour import block:", bool(import_count))
print("Replaced onboarding function:", bool(function_count))
