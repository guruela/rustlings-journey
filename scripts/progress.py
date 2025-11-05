#!/usr/bin/env python3
import argparse, pathlib, re, json, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXER_DIR = ROOT / "exercises"
STATE_FILE = ROOT / ".rustlings-state.txt"  # change if your file has another name/path
PROGRESS_MD = ROOT / "docs" / "PROGRESS.md"
BADGE_SVG = ROOT / "docs" / "badge.svg"
README = ROOT / "README.md"

EXCLUDE_DIRS = {"answers", ".git", "target"}
VALID_EXTS = {".rs"}  # ignore quizzes/md by default

_slug_re = re.compile(r"^([A-Za-z0-9_\-\.]+)")

def read_completed_slugs():
    if not STATE_FILE.exists():
        return set()
    done = set()
    for line in STATE_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line: 
            continue
        m = _slug_re.match(line)
        if not m:
            continue
        slug = m.group(1).removesuffix(".rs")
        done.add(slug)
    return done

def find_all_exercises():
    all_slugs = {}
    if not EXER_DIR.exists():
        return {}
    for path in EXER_DIR.rglob("*"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in VALID_EXTS:
            topic = path.parent.name  # e.g., "variables"
            slug = path.stem          # e.g., "variables1"
            all_slugs.setdefault(topic, set()).add(slug)
    return all_slugs

def percent(n, d):
    return 0 if d == 0 else round((n * 100.0) / d)

def make_badge_svg(pct):
    # Minimal shield-like SVG (no external service)
    label = "rustlings"
    msg = f"{pct}%"
    # crude width calc
    lw = 70
    mw = 48
    w = lw + mw
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{label}: {msg}">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".7"/>
    <stop offset=".1" stop-opacity=".1"/>
    <stop offset=".9" stop-opacity=".3"/>
    <stop offset="1" stop-opacity=".5"/>
  </linearGradient>
  <mask id="a"><rect width="{w}" height="20" rx="3" fill="#fff"/></mask>
  <g mask="url(#a)">
    <rect width="{lw}" height="20" fill="#555"/>
    <rect x="{lw}" width="{mw}" height="20" fill="#4c1"/>
    <rect width="{w}" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{lw/2:.1f}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{lw/2:.1f}" y="14">{label}</text>
    <text x="{lw+mw/2:.1f}" y="15" fill="#010101" fill-opacity=".3">{msg}</text>
    <text x="{lw+mw/2:.1f}" y="14">{msg}</text>
  </g>
</svg>'''

def write_progress_md(summary, per_topic):
    PROGRESS_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Rustlings Progress",
        "",
        f"- **Completed:** {summary['done']} / {summary['total']} ({summary['pct']}%)",
        "",
        "## By Topic",
        "",
        "| Topic | Done | Total | % |",
        "|---|---:|---:|---:|",
    ]
    for topic, stats in sorted(per_topic.items()):
        lines.append(f"| {topic} | {stats['done']} | {stats['total']} | {stats['pct']}% |")
    lines.append("")
    PROGRESS_MD.write_text("\n".join(lines), encoding="utf-8")

def patch_readme(summary):
    if not README.exists():
        return
    content = README.read_text(encoding="utf-8")
    marker = "<!-- RUSTLINGS_PROGRESS -->"
    line = f"![Rustlings Progress](docs/badge.svg)  \n**{summary['done']} / {summary['total']} completed ({summary['pct']}%)**"
    if marker in content:
        content = re.sub(r"<!-- RUSTLINGS_PROGRESS -->.*?<!-- /RUSTLINGS_PROGRESS -->",
                         f"{marker}\n{line}\n<!-- /RUSTLINGS_PROGRESS -->",
                         content, flags=re.S)
    else:
        content += f"\n\n{marker}\n{line}\n<!-- /RUSTLINGS_PROGRESS -->\n"
    README.write_text(content, encoding="utf-8")

def main(update_files=True):
    completed = read_completed_slugs()
    topics = find_all_exercises()

    total = sum(len(v) for v in topics.values())
    done = sum(len(v & completed) for v in topics.values())
    pct = percent(done, total)

    per_topic = {}
    for t, slugs in topics.items():
        d = len(slugs & completed)
        per_topic[t] = {"done": d, "total": len(slugs), "pct": percent(d, len(slugs))}

    summary = {"done": done, "total": total, "pct": pct}

    if update_files:
        BADGE_SVG.parent.mkdir(parents=True, exist_ok=True)
        BADGE_SVG.write_text(make_badge_svg(pct), encoding="utf-8")
        write_progress_md(summary, per_topic)
        patch_readme(summary)

    print(json.dumps({"summary": summary, "topics": per_topic}, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Only print JSON; don't write files")
    args = parser.parse_args()
    main(update_files=not args.dry_run)

