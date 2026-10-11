"""Check local inline Markdown links without third-party dependencies."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
errors = []
count = 0
for document in sorted(ROOT.rglob("*.md")):
    if any(part in {".git", ".venv", "node_modules"} for part in document.relative_to(ROOT).parts):
        continue
    count += 1
    for raw in re.findall(r"\]\(([^)]+)\)", document.read_text()):
        target = raw.strip().split(' "', 1)[0].strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        path = ROOT / unquote(parsed.path).lstrip("/") if parsed.path.startswith("/") else document.parent / unquote(parsed.path)
        if not path.exists():
            errors.append(f"{document.relative_to(ROOT)}: missing target {target}")
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"Checked local links in {count} Markdown documents.")
