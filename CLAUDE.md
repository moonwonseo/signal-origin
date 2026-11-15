# CLAUDE.md

Follow `AGENTS.md` (project rules and layout) and read `docs/HANDOFF.md` before starting work.

## Communication and compute (rules from Celine, 14 Nov 2026)
1. Always write to Celine in ASD-STE100 Simplified Technical English.
2. Make each report concise. Go straight to the point.
3. After each report, give proposed concrete actions.
4. Use the Mac mini for training and for all compute-intensive tasks (see `AGENTS.md`).

Claude-specific notes:
- Celine prefers direct, opinionated answers and honest epistemic standards. When she lists her understanding
  back to you, correct only what is factually wrong, briefly.
- Ask before anything that cannot be undone or that changes Moonwon's work: merging, editing `main`, editing
  V4 modules, the publication allowlist, or signing off `configs/v5_spec.json`.
- Network from the sandbox is limited: NASA POWER, Yahoo, CFTC, Open-Meteo and USDA are usually unreachable.
  Write the download script and have Celine run it on her Mac, then read the output file.
- When a result is disappointing, say so plainly; do not search for variants until something looks good.
  Each new idea gets its own PLAN.md written before data is seen.
- Commit trailer for AI-assisted commits:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
