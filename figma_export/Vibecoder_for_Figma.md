# Vibecoder — Repo Export for Figma

Repository: https://github.com/Madhukar04012/vibecoder/tree/V2

Overview:
- Full-stack AI project generator (FastAPI backend + React frontend).
- Agent pipeline: planner → db_schema → auth → coder → code_reviewer → tester → deployer.

What I attempted:
- Tried to add a Code Connect mapping to Figma file `rWGxqFiZaEy7wNY5GUBqhr` (node `0:1`).
- Figma responded: "You need a Developer seat in an Organization or Enterprise plan to access Code Connect." (Debug UUID provided by Figma.)

If you want the repo content inside the Figma file, options:

1) Grant access (recommended)
- Add a Developer seat for the Figma org or move the file to an Organization/Enterprise plan that has a Developer seat.
- Then I can re-run the Code Connect mapping and link the repo root to the Figma page node `0:1`.

2) Manual paste (works without org seat)
- Open the Figma file and select the page or a frame where you want the code.
- Use the text tool to create a large text area and paste README or file contents directly.
- For many files, use a Figma plugin such as "Paste as plain text" or "Code Block" to preserve formatting.

3) Use a hosted gist or link
- I can generate a single Markdown summary or individual file snippets and you can paste or embed links in Figma.

Included below: repo summary and suggested sections to paste into Figma.

---

## Suggested sections to add into the Figma page

- `README.md` (project summary and usage)
- `AGENTS.md` (explain agents and architecture)
- `backend/` — key files: `backend/main.py`, `backend/api/generate.py`, `backend/agents/` (list of agents)
- `frontend/` — key files: `frontend/src/main.tsx`, `frontend/src/components/NovaIDE.tsx`

If you prefer, tell me which specific files or directories you want exported into the Figma file and I will prepare ready-to-paste Markdown snippets for each.
