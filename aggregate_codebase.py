#!/usr/bin/env python3
"""
aggregate_codebase.py
---------------------
Aggregates an entire codebase into a single text file suitable for use
as LLM context. Generates an ASCII directory tree at the top, then appends
each file's contents in Markdown fenced-code-block format.

Usage:
    python aggregate_codebase.py [root_dir] [output_file]

Defaults:
    root_dir    = current working directory
    output_file = _llm_context.txt
"""

import os
import sys

# ---------------------------------------------------------------------------
# Configuration — tweak these lists as needed
# ---------------------------------------------------------------------------

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "venv",
    "env",
    ".env",
    "__pycache__",
    "node_modules",
    "bower_components",
    ".next",
    ".nuxt",
    "dist",
    "build",
    "out",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "coverage",
    ".coverage",
    "htmlcoverage",
    ".idea",
    ".vscode",
    ".DS_Store",
    "vendor",        # Go, PHP
    "target",        # Rust / Maven
    "bin",
    "obj",           # .NET
    "Pods",          # iOS CocoaPods
}

IGNORED_EXTENSIONS = {
    # Compiled / bytecode
    ".pyc", ".pyo", ".pyd",
    ".class", ".o", ".a", ".so", ".dll", ".exe", ".dylib",
    # Lock files
    ".lock",
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
    ".tiff", ".tif",
    # Fonts
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    # Audio / Video
    ".mp3", ".mp4", ".wav", ".ogg", ".avi", ".mov", ".mkv", ".flac",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".rar", ".7z",
    # Databases / binary data
    ".db", ".sqlite", ".sqlite3", ".dat",
    # Office / PDF
    ".pdf", ".docx", ".xlsx", ".pptx", ".doc", ".xls",
    # Other binary
    ".bin", ".wasm",
    # Minified / map files
    ".min.js", ".min.css", ".map",
}

# Hard-coded output filename that is always excluded
OUTPUT_FILENAME = "_llm_context.txt"

# Max size (bytes) to include a file in full
MAX_FILE_BYTES = 1_000_000  # 1 MB

# Number of lines to preview for oversized files
LARGE_FILE_PREVIEW_LINES = 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def should_skip(path: str, name: str, is_dir: bool) -> bool:
    """Return True if this path should be excluded from the aggregation."""
    if is_dir:
        return name in IGNORED_DIRS
    # Always skip the output file itself
    if name == OUTPUT_FILENAME:
        return True
    # Skip by extension (handle compound extensions like .min.js)
    for ext in IGNORED_EXTENSIONS:
        if name.endswith(ext):
            return True
    return False


def is_binary(filepath: str, sample_bytes: int = 8192) -> bool:
    """
    Heuristic binary check: read a sample of the file and look for null bytes
    or a high ratio of non-printable characters.
    """
    try:
        with open(filepath, "rb") as fh:
            chunk = fh.read(sample_bytes)
    except OSError:
        return True  # Can't read → treat as binary / skip

    if b"\x00" in chunk:
        return True  # Null byte is a strong binary indicator

    # If more than 30 % of bytes are non-text, consider it binary
    non_text = sum(
        1 for b in chunk
        if b < 9 or (14 <= b <= 31) or b == 127
    )
    return (non_text / len(chunk)) > 0.30 if chunk else False


def collect_files(root: str) -> list[str]:
    """
    Walk the directory tree, respecting ignore rules, and return a sorted list
    of relative file paths.
    """
    collected: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Prune ignored directories in-place so os.walk doesn't descend
        dirnames[:] = sorted(
            d for d in dirnames
            if not should_skip(os.path.join(dirpath, d), d, is_dir=True)
        )

        for filename in sorted(filenames):
            if should_skip(os.path.join(dirpath, filename), filename, is_dir=False):
                continue
            rel_path = os.path.relpath(os.path.join(dirpath, filename), root)
            collected.append(rel_path)

    return collected


# ---------------------------------------------------------------------------
# ASCII tree builder
# ---------------------------------------------------------------------------

def build_tree(file_paths: list[str]) -> str:
    """
    Given a flat list of relative file paths, build an ASCII directory tree
    string that mirrors the structure of those files.
    """
    # Represent the tree as nested dicts: {"dir": {"subdir": {}, "file.py": None}}
    tree: dict = {}

    for path in file_paths:
        parts = path.replace("\\", "/").split("/")
        node = tree
        for part in parts[:-1]:          # directories
            node = node.setdefault(part, {})
        node[parts[-1]] = None           # file (leaf)

    lines: list[str] = ["."]

    def _render(node: dict, prefix: str = "") -> None:
        items = sorted(node.keys(), key=lambda k: (node[k] is None, k))
        for idx, name in enumerate(items):
            is_last = idx == len(items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{name}")
            if node[name] is not None:          # directory
                extension = "    " if is_last else "│   "
                _render(node[name], prefix + extension)

    _render(tree)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main aggregation logic
# ---------------------------------------------------------------------------

def aggregate(root: str, output_path: str) -> None:
    print(f"[*] Scanning: {os.path.abspath(root)}")
    files = collect_files(root)
    print(f"[*] Found {len(files)} file(s) to include.")

    skipped_binary = 0
    skipped_large = 0
    written = 0

    with open(output_path, "w", encoding="utf-8") as out:
        # ── Directory tree ──────────────────────────────────────────────────
        out.write("# Codebase Context\n\n")
        out.write("## Directory Structure\n\n")
        out.write("```\n")
        out.write(build_tree(files))
        out.write("\n```\n\n")
        out.write("---\n\n")

        # ── File contents ───────────────────────────────────────────────────
        out.write("## File Contents\n\n")

        for rel_path in files:
            abs_path = os.path.join(root, rel_path)

            # Skip files that are too large
            try:
                file_size = os.path.getsize(abs_path)
            except OSError:
                continue

            if file_size > MAX_FILE_BYTES:
                size_mb = file_size / 1_000_000
                print(f"  [stub-large]  {rel_path}  ({size_mb:.1f} MB) — preview only")
                ext = os.path.splitext(rel_path)[1].lstrip(".")
                out.write(f"### File: {rel_path}\n\n")
                out.write(
                    f"> ⚠️ File too large to include in full ({size_mb:.1f} MB). "
                    f"Showing first {LARGE_FILE_PREVIEW_LINES} lines only.\n\n"
                )
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                        preview_lines = []
                        for _ in range(LARGE_FILE_PREVIEW_LINES):
                            line = fh.readline()
                            if not line:
                                break
                            preview_lines.append(line)
                    preview = "".join(preview_lines)
                    out.write(f"```{ext}\n")
                    out.write(preview)
                    if preview and not preview.endswith("\n"):
                        out.write("\n")
                    out.write("```\n\n")
                except OSError:
                    out.write("_Could not read file preview._\n\n")
                skipped_large += 1
                continue

            # Skip binary files
            if is_binary(abs_path):
                print(f"  [skip-binary] {rel_path}")
                skipped_binary += 1
                continue

            # Read content
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except OSError as exc:
                print(f"  [error]       {rel_path}: {exc}")
                continue

            # Determine language hint for the fenced code block
            ext = os.path.splitext(rel_path)[1].lstrip(".")

            out.write(f"### File: {rel_path}\n\n")
            out.write(f"```{ext}\n")
            out.write(content)
            if content and not content.endswith("\n"):
                out.write("\n")
            out.write("```\n\n")
            written += 1

    print(f"\n[✓] Done.")
    print(f"    Written  : {written} file(s)")
    print(f"    Skipped  : {skipped_binary} binary, {skipped_large} stubbed (preview only)")
    print(f"    Output   : {os.path.abspath(output_path)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    out_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root_dir, OUTPUT_FILENAME)

    if not os.path.isdir(root_dir):
        print(f"Error: '{root_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    aggregate(root_dir, out_file)
