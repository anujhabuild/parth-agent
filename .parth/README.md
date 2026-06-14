# .parth/

Per-project Parth configuration:

- `agents/<name>.md` — project-local agents (frontmatter + body markdown).
- `skills/<name>/SKILL.md` — instruction packs the LLM auto-invokes when
  their `description:` matches the task.
- `settings.json` — overrides for this project (merged over the global
  `~/.config/parth-agent/settings.json`).

See `/agent` and `/skill` for activation and `~/.parth/` for the
user-global counterpart.
