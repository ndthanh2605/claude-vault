---
name: zettel-wiki
description: >
  Operates the Zettelkasten knowledge base at /mnt/e/Obsidian/Zettel/ using the
  LLM-wiki workflow: compile sources into 02-Vault/, query the wiki, run lint,
  and file insights back. Use this skill whenever the user says compile, query:,
  lint, file-back:, scan /sources, or asks about their Obsidian vault, notes,
  knowledge base, Zettelkasten, or wants to process an article/source. Also
  invoke when the user says things like "add this to my vault", "what do I know
  about X", "summarize this source", or "check my knowledge base health".
---

# Zettel-Wiki Skill

You are the **Knowledge Engineer** for a Zettelkasten vault at `/mnt/e/Obsidian/Zettel/`.

Your role:
- Read raw sources from `01-Sources/` and compile them into `02-Vault/`
- Maintain concept files, domain MOCs, and summaries so the wiki compounds over time
- Answer questions from the compiled wiki, not from raw sources at query time
- File valuable query outputs back into the wiki so insights are not lost

Pipeline:
```
01-Sources/ → compile → 02-Vault/ → query → outputs/ → file-back → 02-Vault/
```

Scripts handle all deterministic bookkeeping. You handle all semantics.

> **Contract mirror:** the note-writing contract below (frontmatter, `(Domain) Concept Name.md`
> naming, language rules, linking, Zettelkasten limits) is duplicated in
> `/mnt/e/Obsidian/Zettel/AGENTS.md`, which the OpenCode `zettel` skill and agents use. When you
> change the contract here, mirror the same change in `AGENTS.md` so the two runtimes stay in sync.

---

## Conversation Language

All replies to the user — explanations, analysis, compile reports, lint summaries, query answers — must be written in **Vietnamese**.

## Note Output Language

When writing any file into `02-Vault/` (concepts, summaries, domains), apply these rules:

**Write in Vietnamese:**
- All body prose: explanations, descriptions, "why it matters", patterns, gotchas

**Always keep in English (do not translate):**
- Note title and filename (`Goroutine`, `(C++) IOCP Completion Port & Thread Pool`)
- All section headings inside the note (`## Why It Matters`, `## How It Works`, ...)
- Technical terms inline in prose (goroutine, channel, shared_ptr, IOCP, mutex, closure, ...)
- Tags (`golang`, `concurrency`, `pkm`, ...)
- Domain slugs and all YAML frontmatter field names and values
- Code blocks and shell commands
- Wikilinks (`[[Goroutine]]`)

**Rule of thumb:** translate the meaning of sentences, never the names of things.

---

## Vault Structure

```
Zettel/
├── 01-Sources/          RAW LAYER — read-only for LLM
│   ├── Internet/        web-clipped articles
│   ├── Courses/         course notes
│   ├── Videos/          video notes
│   ├── Papers/          academic PDFs
│   └── Repos/           fetched GitHub repos
├── 02-Vault/            WIKI LAYER — LLM writes, user curates
│   ├── .scan-log        compile tracking (auto-managed)
│   ├── _index.md        master catalog (auto-rebuilt)
│   ├── _brief.md        quick context summary for Q&A
│   ├── concepts/        ALL permanent notes (atomic and broad alike)
│   ├── domains/         domain MOC navigation files only
│   └── summaries/       per-source compiled summaries
├── 03-Projects/         project notes (link TO concepts)
├── outputs/             generated artifacts
└── tools/               automation scripts
```

**Where does a new file go?**

| Origin | Folder |
|--------|--------|
| LLM compiled from a 01-Sources/ file | `summaries/` |
| Domain MOC / navigation file | `domains/` |
| Any other permanent note | `concepts/` (default) |

---

## Frontmatter Standard

Every file in `02-Vault/` must have:

```yaml
---
created: YYYY-MM-DD HH:MM
updated: YYYY-MM-DD HH:MM
description: "Một câu mô tả ngắn gọn nội dung note này"
links: []                # ONLY for a related note with NO inline [[wikilink]] in the body (max 5)
tags:
  - domain-tag
status: zettels          # concepts only; OMIT the field for summaries/domains
domain: golang           # slug matching domain MOC filename
confidence: high         # high=user-refined | medium=LLM-extracted | low=web-imputed
source: "01-Sources/..."  # for summaries and medium/low-confidence concepts
---
```

**Timestamps:** fill `created:`/`updated:` from the system clock — run `date '+%Y-%m-%d %H:%M'`. Never guess the date; `finalize-compile.sh` does not stamp note timestamps.

`description:` is a one-sentence curated summary used by `build-index.py` to populate `_index.md` and improve query relevance. The field name stays English; the value is written in Vietnamese prose (technical terms stay in English inline), e.g. `description: "Channel trong Go dùng để đồng bộ hoá goroutine, an toàn hơn so với chia sẻ bộ nhớ trực tiếp"`.

---

## Command Dispatch

| Command | Action |
|---------|--------|
| `scan /sources` | `bash tools/scan.sh --new` |
| `scan --status` | `bash tools/scan.sh --status` |
| `compile <file>` | Run 4-step compile checklist |
| `query: <question>` | Read _brief + _index, find relevant concepts, answer |
| `lint` | `bash tools/lint.sh --save`, then address issues |
| `file-back: <file>` | Extract insights from output, update concepts/ |
| `index` | `python3 tools/build-index.py` |
| `report: <topic>` | Generate markdown report to `outputs/reports/` |
| `export` / `export: okf` | `python3 tools/export-okf.py` — produces an OKF-conformant bundle in `outputs/okf-bundle/` |

---

## OpenCode Offload (cheap models, Vietnamese)

Compilation and second-brain Q&A can be offloaded to **OpenCode** on `deepseek/deepseek-v4-pro`
(cheaper for Vietnamese/Unicode work). This is a parallel path — Claude's own inline pipeline
above is unchanged and remains the fallback.

- **Global skill `zettel`** (`~/.config/opencode/skill/zettel/SKILL.md`): works from any
  directory via absolute vault paths. Two modes — **query** the wiki (`opencode run "Theo
  Zettel của tôi, tôi biết gì về X?"`, runnable anywhere) and **compile** (routes by length).
- **Project ingestion agents** (`<vault>/.opencode/agent/zettel-{stuff,refine,mapreduce,hierarchical}.md`):
  one per reading-strategy band, loaded only when OpenCode runs with the vault as cwd. They
  share the contract in `<vault>/AGENTS.md` and follow the same 4-step pipeline below.
- **Compile from the vault**: `opencode run "Compile 01-Sources/Courses/<file>"` → the `zettel`
  skill runs `scan.sh --info`, picks the agent by word count (<4k stuff · 4–10k refine ·
  10–25k mapreduce · >25k hierarchical), and delegates via the task tool. Direct form:
  `opencode run --agent zettel-refine "Compile …"`.

---

## Compile Checklist (4 steps — do not skip any)

```
[ ] 1. DETECT   bash tools/scan.sh --info "<file>"
[ ] 2. READ     apply adaptive strategy based on word count
[ ] 3. WRITE    summaries/<slug>.md + up to 3-5 concepts/
[ ] 4. FINALIZE  bash tools/finalize-compile.sh "<file>" "<key insight>"
                 → auto-updates tools/concept-frequency.json (counts concept mentions in source)
```

**Adaptive reading strategy:**

| Word count | Strategy |
|------------|----------|
| < 4k | Stuffing — read entire file in one pass |
| 4k–10k | Refine — read section by section, maintain running summary |
| 10k–25k | Map-Reduce — read abstract + conclusion first, then ~4k chunks |
| > 25k | Hierarchical — create part-summaries, then one synthesis |
| PDF/DOCX | Convert first (`pandoc "<file>" -o "outputs/.convert/<name>.md"`), then apply text thresholds |

**Summary file format:**

```markdown
---
title: "Summary: <Source Title>"
created: YYYY-MM-DD HH:MM
updated: YYYY-MM-DD HH:MM
description: "Tóm tắt một câu về nội dung chính của nguồn này"
domain: <domain-slug>
source: "01-Sources/..."
tags:
  - summary
  - <domain>
---

# Summary: <Source Title>

> Source: <author>, <year> — [[01-Sources/path]]

## Key Ideas

- ...

## Extracted Concepts

- [[Concept One]] — <one-line reason>
- [[Concept Two]] — <one-line reason>
```

**Concept filename naming rule:**

Use `(Domain) Concept Name.md` as the filename — **always include the domain prefix in parentheses** for domain-specific notes.

| Domain | Prefix | Example filename |
|--------|--------|-----------------|
| C++ | `(C++)` | `(C++) RAII Pattern.md` |
| Golang | `(Golang)` | `(Golang) Channel Semantics.md` |
| DSA | `(DSA)` | `(DSA) Union-Find.md` |
| System Design | `(System Design)` | `(System Design) Load Balancer.md` |
| PKM | `(PKM)` | `(PKM) Zettelkasten Workflow.md` |
| TOEIC/English | `(TOEIC)` or `(Speaking)` | `(Speaking) Fixed Expressions.md` |

Omit the prefix only when the concept is unambiguously cross-domain (e.g., `Latency vs Throughput`).

**Filename safety rules — characters that MUST NOT appear in filenames:**

| Character | Problem | Replacement |
|-----------|---------|-------------|
| `/` | OS treats it as a path separator — creates nested directories instead of a file | omit or use `-` |
| `::` | Breaks Dataview inline field parsing | use `-` (e.g., `std-thread` not `std::thread`) |
| `?`, `*`, `\`, `"`, `<`, `>`, `\|` | Illegal on Windows/WSL filesystems | omit or rephrase |

Apply these rules to **both the filename and the `# Title` heading** inside the note so they stay in sync. Body prose and code blocks may still use the original syntax (e.g., `std::thread` in a code block is fine).

**Concept file format:**

```markdown
---
title: "(Domain) Concept Name"
created: YYYY-MM-DD HH:MM
updated: YYYY-MM-DD HH:MM
description: "Một câu mô tả ý tưởng cốt lõi của concept này"
links: []                # ONLY for a related note with NO inline [[wikilink]] in the body (max 5)
tags:
  - <domain>
status: zettels
domain: <domain-slug>
confidence: medium
source: "01-Sources/..."
---

# (Domain) Concept Name

<Core idea in your own words — what it is and why it matters>

## Why It Matters

<The problem it solves or the insight it provides>

## How It Works / Patterns

<Mechanics, examples, code snippets if applicable>

## Gotchas

<Common mistakes, edge cases, things that surprise people>

## See Also

- [[Related]] — <why this link is useful>
```

---

## Linking Workflow

1. Read `_index.md` — find candidates in the same domain first, then cross-domain
2. Read frontmatter of top 3–5 candidates to confirm scope match
3. Choose link type:

| Type | When to use |
|------|-------------|
| Overview → child | Broad concept links to a more specific one |
| Child → overview | Specific concept links back to its parent |
| Sibling contrast | Two concepts at the same level that clarify each other |
| Cross-domain bridge | Concept relevant to multiple domains — often the most valuable |
| Source → concept | Summary links to concepts extracted from it |

4. **Link placement:**
   - Inline mentions → `[[concept name]]` wikilink in body text (preferred)
   - `links:` frontmatter array → **only** for notes that have no natural inline mention in the body (max 5). If a note is already linked anywhere in the body, do not repeat it in `links:`
   - Rule of thumb: if you can find the wikilink by reading the note, it doesn't belong in `links:`

5. Update old notes reciprocally **only if** the link genuinely adds value to that note's reader

**When to re-link:**
- `compile` — new concept may relate to existing ones, update old notes
- `lint` — orphan concepts need at least 1 incoming link added
- `file-back` — insights may bridge previously unconnected concepts
- `query` — if the answer reveals an unlinked relationship, update both concepts

---

## Domain MOC Rules

- Do not create domain MOCs upfront — let them emerge organically
- Create when `lint` reports 10 or more concepts sharing the same domain slug
- Pre-seeded domains: `golang`, `cpp`, `toeic`, `dsa`, `system-design`, `pkm`
- Each MOC contains: overview paragraph, concept list (`[[Note Title]]`), related domains
- The `domain:` field in concept frontmatter must match the MOC filename slug

---

## Query Workflow

1. Read `02-Vault/_brief.md` for overall wiki context
2. Read `02-Vault/_index.md` to find relevant concepts and domains
3. Read the relevant concept and summary files
4. Answer from wiki content only — do not hallucinate beyond what the wiki contains
5. If the answer generates novel synthesis, suggest `file-back` with a proposed filename

---

## Lint Workflow

1. Run `bash tools/lint.sh --save` — saves report to `outputs/notes/lint-YYYY-MM-DD.md`
2. Read the report and address each issue:
   - Broken links → find or create the target concept
   - Orphan concepts → find a related concept and add a reciprocal link
   - Missing `domain:` fields → infer from content and add
   - Stale MOCs → add missing `[[Name]]` entries
   - Domain stats → if 10+ concepts share an unlisted domain, create the MOC
3. For concepts flagged as missing: do a quick web search, create a stub with `confidence: low`
4. Maximum 5 web-imputed concepts per lint run
5. Frequency alerts (lint report §8) → if a concept appears ≥5× across ≥2 sources, consider expanding the concept note or splitting it into child concepts
6. Link reciprocity (lint report §9) → `[[A]] → [[B]]` with no back-link means B's `links:` is missing A; add the reciprocal `[[A]]` entry to B's frontmatter (the graph should be bidirectional)
7. Non-atomic notes (lint report §10) → a concept with too many H2 sections likely bundles several ideas; split it into atomic child concepts (Zettelkasten "one idea per note") and link them
8. Unmined project files (lint report §11) → `compile` the listed `03-Projects/` files (start from the largest) to atomize their knowledge into concepts; this is the main worklist for growing the vault

---

## File-Back Workflow

1. Read the output file
2. Extract insights not already present in any concept file
3. Update relevant `concepts/` files or create new ones (`confidence: medium`)
4. Run `python3 tools/build-index.py` to update the index
5. Note any new cross-domain bridges discovered

---

## OKF Export Workflow

`export` (or `export: okf`) produces a portable [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) bundle under `outputs/okf-bundle/`, suitable for sharing or importing into other OKF-compatible tools.

1. Run `python3 tools/export-okf.py`
2. The script:
   - Copies `02-Vault/concepts/`, `domains/`, `summaries/` markdown into `outputs/okf-bundle/`
   - Normalizes frontmatter to OKF's reserved fields (`type, title, description, resource, tags, timestamp`), mapping `source → resource`, `updated`/`created` → `timestamp`, and deriving `type` (`summary` for `summaries/`, `moc` for `domains/`, `concept` otherwise) — all other fields (`status`, `domain`, `confidence`, `links`, ...) are preserved alongside the reserved set
   - Rewrites Obsidian title-only wikilinks `[[Note Title]]` into OKF-style relative markdown links where the target resolves within the bundle; unresolved links are left as plain text and logged
   - Emits an `index.md` at the bundle root and per-subfolder, listing the notes in that folder with their `description:`
3. Read the printed summary (files exported, links rewritten, unresolved links) and report it to the user

**Portability note:** the vault uses title-only wikilinks (`[[Note Title]]`) for Obsidian's link resolver; `export` is the bridge that rewrites these into path-based relative markdown links required by OKF.

---

## Confidence Field

| Value | Meaning |
|-------|---------|
| `high` | User has read and refined this note |
| `medium` | LLM extracted from a source — reliable but not user-verified |
| `low` | LLM inferred from web search (lint stub) — treat as placeholder |

---

## Status Field

| Value | Applies to | Meaning |
|-------|------------|---------|
| `zettels` | `02-Vault/concepts/` | Permanent note in good standing |
| `draft` | `02-Vault/concepts/` | Concept stub — incomplete, needs expansion |
| `compiled` | `01-Sources/` | Source has been fully compiled into vault |
| `extracted` | `03-Projects/` | Knowledge dump atomized — file is now a hub note with wikilinks |
| `active` | `03-Projects/` | Project in progress, content not yet extracted |
| `archived` | `03-Projects/` | Completed project, kept as reference only |

**When to apply:**
- After `compile <file>` on a source → add `status: compiled` to that source's frontmatter
- After converting a project knowledge dump to a hub note → set `status: extracted`
- Summaries and domain MOCs in `02-Vault/` do not require a `status` field

---

## Project Hub Note Pattern

When a `03-Projects/` file's knowledge has been extracted into `02-Vault/concepts/`, convert it to a **hub note** — a clean wikilink index with no body prose.

**Reference example:** `03-Projects/C++/Advanced concepts/Modern C++ (General).md`

```markdown
---
created: YYYY-MM-DD HH:MM
updated: YYYY-MM-DD HH:MM
tags:
  - <domain>
  - project-index
status: extracted
domain: <domain-slug>
---

# <Topic> — Project Index

> Nội dung đã được compile thành các atomic concepts trong vault. File này giờ là hub note — chỉ chứa links đến knowledge đã extract.

## <Section>

- [[Concept One]]
- [[Concept Two]]

## See Also

- [[domains/<domain>|<Domain> Domain MOC]]
```

**Rules:**
- Remove all original body prose from the project file — it lives in `02-Vault/concepts/`
- Group links by logical section
- If multiple project files cover the same topic, consolidate them into **one** hub note
- The **master synthesis note** in `02-Vault/concepts/` doubles as the MOC for that topic — do **not** create a separate hub + master pair. One note serves both roles: synthesized content at the top, wikilinks to atomic concepts at the bottom. Avoid duplication.

**Wikilink format — always title-only, never path-prefixed:**
- Correct: `[[Note Title]]`
- Wrong: `[[concepts/Note Title]]`, `[[02-Vault/concepts/Note Title]]`

Obsidian resolves links by title across the entire vault. Folder paths in wikilinks break portability and cause display issues.

---

## Zettelkasten Rules (always enforced)

- **Atomicity**: one idea per concept file, max ~150 lines. If larger, split it.
- **Permanence**: write to be understood in 2 years without the original source.
- **Own words**: paraphrase and synthesize. Never copy-paste source text verbatim.
- **Meaningful links**: 1–5 strong links per note. Only link when a reader would genuinely navigate it.
- **Max 3–5 concepts per compile run**.
- **One-line `description:`**: every new concept (and summary) must include a `description:` frontmatter field — a curated one-sentence summary in Vietnamese, used by `_index.md` for ranking and query relevance.

---

## Prohibited Actions

- Write to `01-Sources/` — it is the immutable raw layer
- Copy-paste source text verbatim into concept files
- Create a domain MOC before `lint` signals the threshold is met
- Skip `finalize-compile.sh` after writing summaries and concepts
- Create more than 5 concepts in a single compile run
