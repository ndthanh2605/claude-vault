#!/usr/bin/env python3
"""Maintenance helper for a LEARNINGS.md self-learning file.

Dependency-free (stdlib only). Three commands:

    python learnings.py init       [path]                 create a LEARNINGS.md skeleton
    python learnings.py stats      [path]                 section / confidence / format health
    python learnings.py scan-stale [path] [--days N]      flag old & version-tagged entries

The file format is the one described in references/entry-format.md. Entries look like:

    - [YYYY-MM-DD · tag1,tag2 · conf:high] concrete statement ...

This script only reads and reports (except `init`); it never edits or deletes entries, because
deciding whether a stale-looking learning still applies needs a human.
"""

import argparse
import datetime as dt
import re
import sys

DEFAULT_PATH = "LEARNINGS.md"
MIDDOT = "·"  # the '·' separator used in entry prefixes

SECTIONS = [
    "What Works",
    "What Doesn't Work",
    "Codebase Patterns",
    "Tool & Library Notes",
    "Recurring Errors & Fixes",
    "Session Notes",
    "Open Questions",
]

TEMPLATE = """# Project Learnings — {name}

> Durable operational knowledge for this codebase. Read it before substantial work; capture concrete,
> anchored learnings after. See the self-learning skill for the loop and entry format.

## What Works
<!-- Approaches, patterns, and solutions that have proven effective here -->

## What Doesn't Work
<!-- Failed approaches, dead ends, antipatterns to avoid -->

## Codebase Patterns
<!-- Project-specific conventions, architecture decisions, naming -->

## Tool & Library Notes
<!-- Quirks, gotchas, and useful behaviors of dependencies (pin versions) -->

## Recurring Errors & Fixes
<!-- Errors seen more than once and their resolutions -->

## Session Notes
<!-- Dated, one-line summaries of what each session accomplished -->

## Open Questions
<!-- Unresolved things, left for a future session -->
"""

DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
ENTRY_RE = re.compile(r"^\s*-\s+\[([^\]]*)\]\s*(.*)$")
HEADING_RE = re.compile(r"^##\s+(.*?)\s*$")
# a tag that pins a version, e.g. react-18, passport-jwt-v4, node20 — i.e. contains a digit
VERSIONED_TAG_RE = re.compile(r"[A-Za-z].*\d")


class Entry:
    def __init__(self, section, lineno, prefix, body):
        self.section = section
        self.lineno = lineno
        self.prefix = prefix
        self.body = body
        self.date = None
        self.tags = []
        self.conf = None
        self.malformed = False
        self._parse_prefix(prefix)

    def _parse_prefix(self, prefix):
        m = DATE_RE.search(prefix)
        if m:
            try:
                self.date = dt.date.fromisoformat(m.group(1))
            except ValueError:
                self.date = None
        parts = [p.strip() for p in prefix.split(MIDDOT)]
        for part in parts:
            if not part:
                continue
            if DATE_RE.fullmatch(part):
                continue
            if part.lower().startswith("conf:"):
                self.conf = part.split(":", 1)[1].strip().lower()
            elif "," in part or VERSIONED_TAG_RE.search(part) or part.replace("-", "").isalnum():
                self.tags.extend(t.strip() for t in part.split(",") if t.strip())
        # A well-formed entry at minimum carries a parseable date.
        self.malformed = self.date is None

    def versioned_tags(self):
        return [t for t in self.tags if VERSIONED_TAG_RE.search(t)]


def parse(path):
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        sys.exit(f"error: {path} not found. Run `learnings.py init {path}` to create one.")
    entries = []
    section = "(no section)"
    for i, line in enumerate(lines, 1):
        h = HEADING_RE.match(line)
        if h:
            section = h.group(1)
            continue
        e = ENTRY_RE.match(line)
        if e:
            entries.append(Entry(section, i, e.group(1), e.group(2)))
    return entries


def cmd_init(args):
    path = args.path
    try:
        with open(path, "x", encoding="utf-8") as fh:
            name = re.sub(r"[-_]", " ", path.rsplit("/", 1)[-1].rsplit(".", 1)[0]) or "project"
            fh.write(TEMPLATE.format(name=name))
    except FileExistsError:
        sys.exit(f"refusing to overwrite existing {path}")
    print(f"created {path} with {len(SECTIONS)} sections")


def cmd_stats(args):
    entries = parse(args.path)
    if not entries:
        print("no entries yet")
        return
    by_section = {s: 0 for s in SECTIONS}
    by_conf = {"high": 0, "med": 0, "low": 0, "(none)": 0}
    malformed = []
    for e in entries:
        by_section[e.section] = by_section.get(e.section, 0) + 1
        by_conf[e.conf if e.conf in by_conf else "(none)"] += 1
        if e.malformed:
            malformed.append(e)

    total = len(entries)
    print(f"{total} entries in {args.path}\n")
    print("by section:")
    for s in SECTIONS:
        print(f"  {by_section.get(s, 0):3d}  {s}")
    extra = sorted(set(by_section) - set(SECTIONS))
    for s in extra:
        print(f"  {by_section[s]:3d}  {s}  (non-standard section)")
    print("\nby confidence:")
    for c in ("high", "med", "low", "(none)"):
        print(f"  {by_conf[c]:3d}  {c}")

    # Health signals — surface patterns worth acting on, not just logging more.
    neg = by_section.get("What Doesn't Work", 0) + by_section.get("Recurring Errors & Fixes", 0)
    if total and neg / total > 0.4:
        print(f"\nsignal: {neg}/{total} entries are failures/errors (>40%) — the base approach may "
              "need attention, not just more learnings.")
    if by_section.get("Open Questions", 0) >= 8:
        print(f"\nsignal: {by_section['Open Questions']} open questions are piling up — consider "
              "resolving or pruning some.")
    if malformed:
        print(f"\n{len(malformed)} entr(y/ies) missing a parseable [YYYY-MM-DD ...] prefix:")
        for e in malformed[:10]:
            print(f"  line {e.lineno}: {e.body[:70]}")


def cmd_scan_stale(args):
    entries = parse(args.path)
    today = dt.date.today()
    horizon = today - dt.timedelta(days=args.days)
    old = [e for e in entries if e.date and e.date < horizon]
    versioned = [e for e in entries if e.versioned_tags()]

    print(f"scanning {args.path} (horizon: {args.days} days, before {horizon.isoformat()})\n")
    if old:
        print(f"{len(old)} entr(y/ies) older than {args.days} days — review whether still true:")
        for e in sorted(old, key=lambda x: x.date):
            print(f"  [{e.date}] ({e.section}) {e.body[:70]}")
    else:
        print(f"no entries older than {args.days} days.")
    if versioned:
        print(f"\n{len(versioned)} version-tagged entr(y/ies) — discount these after a stack upgrade:")
        for e in versioned:
            print(f"  {','.join(e.versioned_tags())}: {e.body[:60]}")
    print("\n(this command only reports — it never edits the file.)")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", help="create a LEARNINGS.md skeleton")
    pi.add_argument("path", nargs="?", default=DEFAULT_PATH)
    pi.set_defaults(func=cmd_init)

    ps = sub.add_parser("stats", help="section / confidence / format health")
    ps.add_argument("path", nargs="?", default=DEFAULT_PATH)
    ps.set_defaults(func=cmd_stats)

    pt = sub.add_parser("scan-stale", help="flag old & version-tagged entries")
    pt.add_argument("path", nargs="?", default=DEFAULT_PATH)
    pt.add_argument("--days", type=int, default=90, help="staleness horizon in days (default 90)")
    pt.set_defaults(func=cmd_scan_stale)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
