# claude-vault

Version-controlled backup of the portable, reusable parts of my `~/.claude`
configuration for [Claude Code](https://claude.com/claude-code).

This repo is the contents of `~/.claude` itself — clone it *as* that directory (see
[Restore](#restore-on-a-new-machine)). A whitelist `.gitignore` keeps everything secret,
private, large, or machine-generated out of version control.

## What's in here

| Path | Contents |
|------|----------|
| `CLAUDE.md` | Global instructions applied to every project |
| `settings.json` | Main config: model, hooks, enabled plugins, marketplaces, theme |
| `skills/` | Authored skills only (plugin-provided symlinked skills are excluded) |
| `hooks/` | Custom hook scripts (`.cjs`, `.mjs`, `.py`) |
| `agents/` | Custom agent definitions (placeholder for now) |

## What's deliberately **not** here

Excluded by `.gitignore` and never committed:

- **Secrets** — `.credentials.json` (OAuth tokens), `mcp-needs-auth-cache.json`
- **Private data** — `history.jsonl`, `projects/` (conversation transcripts), `sessions/`,
  `.remember/`, `file-history/`, `shell-snapshots/`, `session-env/`, `ide/`, `tasks/`,
  `paste-cache/`
- **Plugins** — the entire `plugins/` folder (caches + manifests). Plugins are reinstalled,
  not versioned (see below).
- **Regenerable caches** — `context-mode/`, `cache/`, `downloads/`, `backups/`
- **Work plans** — `plans/`
- **Plugin-provided skills** — any `skills/*` entry that is a symlink into
  `../../.agents/skills/`

## Restore on a new machine

```bash
git clone https://github.com/ndthanh2605/claude-vault.git ~/.claude
```

Then:

1. **Re-authenticate** Claude Code (`.credentials.json` is intentionally not in the repo).
2. **Reinstall plugins.** The `plugins/` folder is not versioned. The set of enabled
   plugins and their marketplaces is recorded in `settings.json` under `enabledPlugins`
   and `extraKnownMarketplaces` — reinstall via `claude plugin install` / `/plugin`.
3. **Fix machine-specific paths.** `settings.json` contains hardcoded absolute paths
   (`/home/hypocrite/...` in the `hooks` commands and the `statusLine` command). Adjust
   these to the new user/home directory.

## Adding a new authored skill

The `skills/` whitelist in `.gitignore` lists each authored skill explicitly. After
creating a new authored (non-symlink) skill, add a matching line:

```gitignore
!/skills/<your-new-skill>/
```

This keeps future plugin symlinks from being committed automatically.
