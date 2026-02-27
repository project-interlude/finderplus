# Finder+

A fast, lightweight desktop file search utility built with Python and PySide6. Finder+ goes beyond basic filename matching — it searches inside file contents, supports regex and fuzzy matching, previews files inline, and handles directories with tens of thousands of files without freezing the UI.

---

## Screenshot

> Add a screenshot here — `assets/screenshot.png`

---

## Why Finder+

Windows Search is slow and indexes in the background. macOS Spotlight is opinionated about what it surfaces. Most third-party tools are either bloated, paid, or require elevated permissions to install.

Finder+ is a single Python file. It runs from source or as a compiled standalone executable. There are no background services, no indexing, no telemetry, and no installation required. It scans on demand, only when you ask it to.

---

## Features

### Search Modes

**Filename search (default)**
The baseline mode. Scans every filename in the selected directory tree recursively and returns any file whose name contains the query string. Case-insensitive by default. Matched results appear in real time as the scan progresses.

**Content search**
Toggle the `[ ]` button to search inside file contents in addition to filenames. Finder+ reads the raw text of each file and scans for the query string. Up to three snippet matches per file are extracted with surrounding context (60 characters either side) and surfaced as a tooltip on the result row. Content search is capped at 5 MB per file to avoid stalling on large logs or data dumps. Supported file types span 50+ extensions including all common source code, config, markup, and data formats.

**Fuzzy matching**
Powered by the `rapidfuzz` library. Uses `partial_ratio` scoring to find filenames that approximately match the query — useful when you remember part of a filename but not the exact spelling. A configurable threshold slider (0–100) controls sensitivity. Disabled gracefully if `rapidfuzz` is not installed, with a clear tooltip explaining why.

**Regex mode**
Full Python `re` module regex support applied to filenames. When content search is also active, the same compiled pattern is used against file contents. Invalid patterns are caught and reported in the status bar without crashing. Case sensitivity is respected via `re.IGNORECASE`.

**Case-sensitive toggle**
All search modes (plain, fuzzy, regex, content) respect the case sensitivity flag. When off, comparisons are lowercased before matching. When on, exact casing is required.

---

### Filtering

**Extension filter**
Space or comma-separated list of file extensions. Accepts `.py .js .txt` or `.py,.js,.txt`. Filtering is applied before any content is read, so it meaningfully speeds up content searches on large directories.

**Date range filter**
Filter by last-modified date using `YYYY-MM-DD` format. Both start and end dates are optional — you can specify just one to create an open-ended range. Dates are validated before the search starts, with an error shown in the status bar if the format is wrong.

**File size filter**
Min and max size in kilobytes. Useful for finding large files eating disk space, or filtering out empty placeholder files. Both bounds are optional.

**Result limit**
Configurable maximum result count (default 5,000). Prevents runaway scans on enormous directory trees. When the limit is hit, the status bar reports it clearly.

---

### Sorting

Results can be sorted by:

- **Relevance** — fuzzy match score descending (most relevant first). For non-fuzzy searches all scores are equal so order reflects scan order.
- **Name** — alphabetical ascending
- **Date** — last-modified descending (newest first)
- **Size** — largest first
- **Extension** — grouped by file type, then alphabetical within each group

Sorting is applied after the full scan completes, not during, so it never slows the search itself.

---

### Results Panel

**Tree view with columns**
Results are displayed in a four-column tree: Name, Path, Size, Modified. The Name column is color-coded by file extension — 40+ extension-to-color mappings cover every common file type. Python files are blue, JavaScript amber, Rust orange, Markdown indigo, and so on. This makes it easy to visually scan a mixed result set.

**Group by folder**
Toggle to collapse results into folder groups, each showing the count of matched files inside. Folders are sorted alphabetically and auto-expanded. Useful when searching a monorepo or any directory with a deep, structured hierarchy.

**Content match indicator**
When a result was found via content search rather than filename match, its path cell turns green and a tooltip shows the first matched snippet in context. This makes it immediately obvious why a file appeared in the results.

**Multi-select**
Standard extended selection — click, shift-click, ctrl-click. All context menu actions operate on the full selection.

**Right-click context menu**
- Open file — launches in the system default application
- Open containing folder — opens the parent directory in Explorer/Finder
- Copy path — copies the full absolute path of the first selected file
- Copy filename — copies just the filename
- Copy all paths — copies newline-separated paths of all selected files (useful for piping into other tools)

**Double-click to open**
Double-clicking any result opens it immediately in the system default application.

---

### Preview Panel

Selecting any result loads its contents into the preview pane on the right. The preview:

- Loads up to 500 KB of file content, with a truncation notice if the file is larger
- Uses a monospaced font for accurate rendering of code and structured text
- Highlights all query matches using a `QSyntaxHighlighter` subclass — matches are highlighted amber with dark brown text, consistent whether the search was plain string, regex, or case-sensitive
- Auto-scrolls to the first match in the file
- Gracefully handles binary files and unsupported extensions with a plain message instead of garbled output

---

### Export

Results can be exported in two formats:

- **Plain text** — one absolute path per line, with a header showing the folder, query, result count, and export timestamp
- **CSV** — structured with columns for Name, Path, Size (bytes), Modified date, and Extension. Ready to open in Excel or import into any data tool.

---

### Non-blocking Search

The entire scan runs in a `QThread` worker, completely separate from the UI thread. The interface stays fully responsive during long searches — you can adjust filters, scroll existing results, or press Escape to abort at any point. A thin progress bar at the top of the window updates every 300 files to show scan progress. The status bar reports the total file count found, elapsed time in seconds, and any warnings.

A 320ms debounce timer on all inputs means the search does not fire on every keystroke — it waits for a short pause before starting, avoiding redundant scans while you are still typing.

---

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+L` | Focus the search bar |
| `Ctrl+R` | Toggle regex mode |
| `Ctrl+F` | Toggle fuzzy match |
| `Ctrl+Shift+F` | Toggle content search |
| `Ctrl+Shift+C` | Toggle case sensitive |
| `Ctrl+O` | Open folder picker |
| `Ctrl+E` | Export results |
| `Escape` | Abort running search |

---

## Tech Stack

| Component | Library |
|---|---|
| UI framework | PySide6 (Qt6 Python bindings) |
| Fuzzy matching | rapidfuzz |
| Search execution | QThread (non-blocking) |
| Syntax highlighting | QSyntaxHighlighter |
| Build / distribution | PyInstaller |

---

## Installation

### Run from source

```bash
git clone https://github.com/you/finder-plus
cd finder-plus
pip install PySide6 rapidfuzz
python finderplus.py
```

`rapidfuzz` is optional. If it is not installed, fuzzy matching is disabled and all other features work normally.

### Build standalone executable (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Finder+" finderplus.py
```

The executable will be at `dist/Finder+.exe`. No Python installation required on the target machine.

If you encounter missing module errors when running the compiled exe, use:

```bash
pyinstaller --onefile --windowed --name "Finder+" --collect-all PySide6 finderplus.py
```

---

## Requirements

- Python 3.9 or later
- PySide6
- rapidfuzz (optional, for fuzzy matching)

---

## License

MIT
