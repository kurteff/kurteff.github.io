#!/usr/bin/env python3

# Usage
# -------------------
# # Using defaults (bib.json + references.cfg)
# python bib_to_html.py

# # Define custom bibliography
# python bib_to_html.py my_bib.json

# # Define custom bibliography + custom config
# python bib_to_html.py my_bib.json --config my_refs.cfg

import json
import argparse
import configparser
from pathlib import Path
from html import escape

# Helper funcs
def format_authors(authors):
    formatted = [a["formatted"] for a in authors]

    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return " & ".join(formatted)
    else:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]

def format_header(authors, year):
    first_author = authors[0]["last"]
    return f"{first_author} et al., {year}" if len(authors) > 1 else f"{first_author}, {year}"

def get_doi_url(entry):
    if entry.get("doi"):
        return f"https://doi.org/{entry['doi']}"

    for u in entry.get("url", []):
        if "doi.org" in u:
            return u

    return None

def entry_to_html(entry):
    authors = entry.get("author", [])
    year = entry.get("published", {}).get("year", "n.d.")
    title = entry.get("title", "")
    journal = entry.get("journalfull") or entry.get("journal", "")
    doi_url = get_doi_url(entry)

    header = format_header(authors, year)
    author_str = format_authors(authors)

    lines = [
        "<section>",
        f"  <h3>{escape(header)}</h3>",
        f"  <p>{escape(author_str)} ({escape(year)}). "
        f"{escape(title)}. <i>{escape(journal)}</i>.</p>"
    ]

    if doi_url:
        lines.extend([
            "  <ul class=\"actions\">",
            f"    <li><a href=\"{escape(doi_url)}\" "
            f"class=\"button\" target=\"_blank\">DOI</a></li>",
            "  </ul>"
        ])

    lines.append("</section>")
    return "\n".join(lines)

def load_citekeys(cfg_path):
    config = configparser.ConfigParser()
    config.read(cfg_path)

    citekeys = config.get("citations", "citekeys", fallback="")
    return [ck.strip() for ck in citekeys.splitlines() if ck.strip()]

def build_html(json_path, citekeys):
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"Bibliography not found: {json_path}")

    with open(json_path, "r") as f:
        entries = json.load(f)

    def norm(s):
        return s.strip() if isinstance(s, str) else None

    entry_map = {
        norm(e.get("citekey")): e
        for e in entries
        if e.get("citekey")
    }

    sections = []
    for ck in citekeys:
        ck_norm = norm(ck)
        if ck_norm not in entry_map:
            print(f"⚠️  Missing citekey: {ck_norm}")
            continue
        sections.append(entry_to_html(entry_map[ck_norm]))

    return "\n\n".join(sections)


# Script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate HTML references from a JSON bibliography"
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        default="bib.json",
        help="Path to bibliography JSON file"
    )
    parser.add_argument(
        "--config",
        default="references.cfg",
        help="Config file with citekeys (default: references.cfg)"
    )

    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    citekeys = load_citekeys(cfg_path)
    html = build_html(args.json_path, citekeys)

    print(html)

