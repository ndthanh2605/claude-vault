# Global Claude Instructions

## Language

Converse with me in Vietnamese — all chat, discussion, explanations, summaries,
and questions directed at me are in Vietnamese. But every underlying artifact
stays in English: code, comments, identifiers, commit messages, PR titles and
bodies, file and doc content, plan files, test names, and any text written to
disk or sent to external systems. In short: **talk to me in Vietnamese, do the
work in English.**

## Code Navigation & Understanding

When working in a codebase where GitNexus has been indexed (check for a `.gitnexus/` directory or `gitnexus://repo/...` resources), **prefer GitNexus over grep/glob/file-reading** for traversal, search, and understanding:

| Task | Use instead of |
|------|---------------|
| Find code by concept/behavior | `gitnexus_query({query: "..."})` instead of `grep` |
| Understand a symbol's role | `gitnexus_context({name: "..."})` instead of reading callers manually |
| Trace an execution flow | `READ gitnexus://repo/{repo}/process/{name}` instead of following call chains by hand |
| Explore what areas exist | `READ gitnexus://repo/{repo}/clusters` instead of `ls`-ing directories |

GitNexus returns process-grouped, relevance-ranked results that reflect the actual call graph — far more accurate than text search for understanding *how* code works vs. just *where* a string appears.


> **Tool priority:** context-mode (`ctx_batch_execute`, `ctx_search`) is the primary tool for all output filtering and context management. When context-mode MCP tools are unavailable, fall back to native Bash/Read (see the discipline rules below).

## Context Window Management (context-mode)

When context-mode is active (session system prompt contains `<context_window_protection>`):

| Task | Use | NOT |
|------|-----|-----|
| Research / explore codebase | `ctx_batch_execute` | Bash with >20-line output |
| Follow-up questions on findings | `ctx_search` | Re-running commands |
| Fetch web docs | `ctx_fetch_and_index` | WebFetch |
| Analyze large files/logs | `ctx_execute_file` | Read |
| Create/edit files | Write / Edit (native) | ctx_execute |

**Hard rules:**
- Never use Bash for commands producing >20 lines of output — use `ctx_batch_execute` instead
- Never use Read for analysis — Read is only for files you're about to Edit
- After `/clear` or `/compact`: tell the user "context-mode knowledge base preserved. Use `ctx purge` to start fresh."

**Discipline rules (learned from session analysis):**
- Never use `Bash cat` or `Bash cat file1 && cat file2` to read multiple files for analysis — one `ctx_batch_execute` handles all of them and keeps output in sandbox
- Always batch `ctx_search` queries: pass multiple strings in the `queries` array in a single call, never fire one query at a time
- Run `ctx_doctor` (or check MCP tool availability with ToolSearch) at the start of any heavy implementation phase — catch a disconnected server before it causes uncontrolled context growth
- If context-mode MCP tools become unavailable mid-session: flag it to the user immediately and ask whether to restart before falling back to direct Bash/Read calls
- Diagnostic sweeps across ≥2 files where none will be edited this turn (e.g. tracing a bug
  through config + frontend + backend): one `ctx_batch_execute` call, one `cat <file>` per
  file, plus `queries` for the specific question — not N sequential `Read` calls. If a file
  turns out to need editing, `Read` it then (Edit requires it).
- Background-task output files (`*.output` from `cargo`/`pytest`/build logs): `ctx_execute_file`,
  never `Read` or `Bash cat`/`tail` — extract the pass/fail line via `queries` instead of
  pulling the full log into context.