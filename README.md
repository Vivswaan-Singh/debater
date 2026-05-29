# Debater 🗣️⚔️

A multi-agent AI pipeline that routes every prompt through a 3-round peer-review loop between **Claude** (Anthropic) and **Codex** (OpenAI) before showing you a final answer.

---

## How It Works

```
Your prompt
    │
    ▼
[Round 1] Claude drafts an answer
    │
    ▼
[Round 2] Codex critiques the draft — bugs, edge cases, performance issues
    │
    ▼
[Round 3] Claude incorporates valid critique → final output
    │
    ▼
You see a peer-reviewed response
```

Every session is token-efficient via caveman compression (see [Acknowledgements](#acknowledgements)) — both agents are primed at session start to communicate in compressed mode, cutting output tokens ~65% across all 3 rounds.

---

## Requirements

- Python 3.10+
- [Claude Code CLI](https://claude.ai/code) installed and authenticated
- [Codex CLI](https://github.com/openai/codex) installed and authenticated

---

## Setup

Two files needed alongside `debater.py`:
```
debater.py
caveman.md
```

Binary paths are set directly in `debater.py` at the top:
```python
CLAUDE_BIN = os.path.expanduser("~/.local/bin/claude")
CODEX_BIN  = os.path.expanduser("~/.nvm/versions/node/<version>/bin/codex")
```

Update these to match your system before running.

---

## Usage

```bash
# Fresh session
python3 /path/to/debater.py

# Resume a previous session
python3 /path/to/debater.py --resume debater-<id> <codex-uuid>

# Exit — prints session IDs so you can resume later
❯ /exit
```

On exit or `Ctrl+C`, debater prints both session identifiers.

---

## Running From Any Directory

Add to `~/.zshrc`:
```bash
alias debater="python3 /path/to/aiTool/debater.py"
```

Then `source ~/.zshrc` and run `debater` from anywhere.

---

## Architecture Notes

- `call_claude()` — shells out to `claude --print` with named session (`-n` on first call, `--resume` after)
- `call_codex()` — shells out to `codex exec` / `codex exec resume <id>`, captures session UUID from stderr on first run
- Both agents are primed with caveman compression rules on fresh session init — rules persist in session history, never re-injected on `--resume`
- `--print` mode means Claude has no file system access — all output is text only, nothing written to disk

---

## Acknowledgements

The token compression strategy used in debater is borrowed from the **[Caveman](https://github.com/getinstachip/caveman)** project — an open-source skill by **[JuliusBrussee](https://github.com/juliusbrussee/caveman)** that makes AI agents communicate in compressed, fragment-heavy prose while preserving full technical accuracy, cutting output tokens by ~65-75%.

Debater uses a trimmed `full`-mode version of the caveman ruleset (`caveman.md`), injected as a priming prompt into both Claude and Codex at session start. No global caveman install required — the rules live entirely inside the session context.

All credit for the compression approach and benchmarking methodology goes to the Caveman authors.
