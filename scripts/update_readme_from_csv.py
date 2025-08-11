#!/usr/bin/env python3
"""
Generate a Markdown table in README.md from a projects CSV.

CSV must have headers (exact):
Project,Date,Tools,Tags,Description,Link

README must contain these markers:
<!-- PROJECTS_TABLE:START -->
<!-- PROJECTS_TABLE:END -->
"""

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import List, Dict

START = "<!-- PROJECTS_TABLE:START -->"
END = "<!-- PROJECTS_TABLE:END -->"

REQUIRED_COLS = ["Project", "Date", "Tools", "Tags", "Description", "Link"]


def read_csv_rows(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLS if c not in cols]
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}. Found: {cols}")
        rows = [dict(r) for r in reader]
    return rows


def normalize_date_for_sort(d: str) -> str:
    """
    Accepts 'YYYY' or 'YYYY-MM'. Returns normalized 'YYYY-MM' for sorting.
    If invalid or empty, return '0000-00' so they end up last.
    """
    d = (d or "").strip()
    if len(d) == 4 and d.isdigit():
        return f"{d}-12"
    if len(d) == 7 and d[4] == "-" and d[:4].isdigit() and d[5:7].isdigit():
        return d
    return "0000-00"


def esc(s: str) -> str:
    """Escape pipes for Markdown table cells."""
    return (s or "").replace("|", r"\|").strip()


def build_table(rows: List[Dict[str, str]]) -> str:
    # Sort newest first by Date
    for r in rows:
        r["_sort_date"] = normalize_date_for_sort(r.get("Date", ""))
    rows.sort(key=lambda x: x["_sort_date"], reverse=True)

    header = "| Project | Date | Tools | Tags | Description |\n|---|---|---|---|---|"
    lines = [header]
    for r in rows:
        name = esc(r.get("Project", ""))
        link = esc(r.get("Link", ""))
        date = esc(r.get("Date", ""))
        tools = esc(r.get("Tools", ""))
        tags = esc(r.get("Tags", ""))
        desc = esc(r.get("Description", ""))
        project_md = f"**[{name}]({link})**" if link else f"**{name}**"
        lines.append(f"| {project_md} | {date} | {tools} | {tags} | {desc} |")

    now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"_Last updated: {now}_")
    return "\n".join(lines)


def insert_between_markers(readme_text: str, block: str,
                           start_marker: str = START, end_marker: str = END) -> str:
    # If markers exist, replace block; otherwise append at end with markers
    section = f"{start_marker}\n{block}\n{end_marker}"
    if start_marker in readme_text and end_marker in readme_text:
        pre = readme_text.split(start_marker)[0].rstrip()
        post = readme_text.split(end_marker)[1].lstrip()
        return f"{pre}{section}{post}"
    else:
        if readme_text and not readme_text.endswith("\n\n"):
            readme_text += "\n"
        return f"{readme_text}\n{section}\n"


def main():
    p = argparse.ArgumentParser(description="Update README table from CSV.")
    p.add_argument("--csv", default="projects.csv", help="Path to CSV (default: projects.csv)")
    p.add_argument("--readme", default="README.md", help="Path to README (default: README.md)")
    p.add_argument("--dry-run", action="store_true", help="Print output to stdout, do not write README")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    args = p.parse_args()

    csv_path = Path(args.csv).resolve()
    readme_path = Path(args.readme).resolve()

    if args.verbose:
        print(f"[i] CSV: {csv_path}")
        print(f"[i] README: {readme_path}")

    rows = read_csv_rows(csv_path)
    if args.verbose:
        print(f"[i] Rows read: {len(rows)}")
        if rows:
            print(f"[i] First row: {rows[0]}")

    table_block = build_table(rows)

    if args.dry_run:
        print("----- GENERATED TABLE START -----")
        print(table_block)
        print("----- GENERATED TABLE END -----")
        return

    if not readme_path.exists():
        # Create an empty README with markers if missing
        readme_text = ""
    else:
        readme_text = readme_path.read_text(encoding="utf-8")

    new_text = insert_between_markers(readme_text, table_block)

    if new_text != readme_text:
        readme_path.write_text(new_text, encoding="utf-8")
        print("README updated from CSV.")
    else:
        print("No README changes detected.")


if __name__ == "__main__":
    main()
