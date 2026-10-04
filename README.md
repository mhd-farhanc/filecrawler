# 🗂️ FileCrawler

> Bundle your entire codebase into a single, LLM-ready context file — in one command.

FileCrawler walks your project directory and produces a neatly formatted `_llm_context.txt` file containing an **ASCII directory tree** followed by every readable source file wrapped in Markdown fenced code blocks. Paste it straight into any LLM (ChatGPT, Claude, Gemini…) and get answers grounded in your full codebase.

---

## ✨ Features

- **ASCII Directory Tree** — A visual map of your project structure is printed at the top of the output so the LLM immediately understands the layout.
- **Markdown Formatting** — Every file is appended as `### File: path/to/file` with its contents in triple-backtick fenced blocks, including a language hint for syntax highlighting.
- **Junk Filtering** — Hardcoded ignore lists skip noisy directories (`node_modules`, `.git`, `venv`, `__pycache__`, `dist`, …) and useless extensions (`.lock`, `.pyc`, images, archives, fonts, binaries, …).
- **Binary Detection** — Files are sampled before reading; anything detected as binary is skipped cleanly — no `UnicodeDecodeError` crashes.
- **Oversized File Guard** — Files larger than 1 MB are never fully included, but they're not silently dropped either. The script writes a stub entry with a warning and the **first 50 lines as a preview**, so the LLM still knows the file exists and can understand its structure.
- **Zero Dependencies** — Pure Python standard library. No `pip install` required.

---

## 🚀 Usage

```bash
# Scan the current directory → writes _llm_context.txt
python aggregate_codebase.py

# Scan a specific project folder
python aggregate_codebase.py /path/to/your/project

# Custom output file
python aggregate_codebase.py /path/to/your/project my_context.txt
```

### Example output structure

```
# Codebase Context

## Directory Structure

\```
.
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
└── README.md
\```

---

## File Contents

### File: src/main.py

\```py
# ... file contents ...
\```
```

---

## ⚙️ Configuration

All filtering is controlled by two sets at the top of `aggregate_codebase.py` — no config file needed, just edit and save.

### Ignored directories (default)

| Category | Directories |
|---|---|
| Version control | `.git`, `.hg`, `.svn` |
| Python | `venv`, `.venv`, `env`, `__pycache__`, `.tox`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache` |
| JavaScript | `node_modules`, `bower_components`, `.next`, `.nuxt` |
| Build output | `dist`, `build`, `out` |
| IDE | `.idea`, `.vscode` |
| Package managers | `vendor` (Go/PHP), `target` (Rust/Maven), `Pods` (iOS) |

### Ignored extensions (default)

| Category | Extensions |
|---|---|
| Compiled / bytecode | `.pyc`, `.pyo`, `.class`, `.o`, `.so`, `.dll`, `.exe` |
| Lock files | `.lock` |
| Images | `.png`, `.jpg`, `.gif`, `.svg`, `.ico`, `.webp`, … |
| Fonts | `.ttf`, `.otf`, `.woff`, `.woff2` |
| Audio / Video | `.mp3`, `.mp4`, `.wav`, `.avi`, … |
| Archives | `.zip`, `.tar`, `.gz`, `.rar`, `.7z` |
| Databases | `.db`, `.sqlite`, `.sqlite3` |
| Minified | `.min.js`, `.min.css`, `.map` |

---

## 💡 When to use it

FileCrawler works best on **small-to-medium projects** (roughly under 5,000 lines of code). At that scale you get the most out of it — the LLM can see your entire codebase at once and give answers that would otherwise take 10 back-and-forth messages.

For larger repos, point it at a **subfolder** rather than the whole project to keep the context focused and within the LLM's token limit.

---

## 📋 Requirements

- Python **3.10+** (uses `list[str]` type hints)
- No third-party packages

---

## 📄 License

MIT — free to use, modify, and distribute.
