import sys
import os
import re
from datetime import datetime
from pathlib import Path

import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("finderplus.app")

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QPushButton, QFileDialog, QFrame, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QStatusBar, QComboBox,
    QSpinBox, QMenu, QHeaderView, QMainWindow,
    QAbstractItemView, QProgressBar
)
from PySide6.QtGui import (
    QFont, QDesktopServices, QAction, QKeySequence, QColor,
    QSyntaxHighlighter, QTextCharFormat, QPalette, QCursor
)
from PySide6.QtCore import Qt, QUrl, QThread, Signal, QTimer

try:
    from rapidfuzz import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# ══════════════════════════════════════════════════════════════
#  PALETTE
#  bg:          #ffffff   (pure white)
#  surface:     #f7f8fc   (off-white panels)
#  text:        #1a1a2e   (near-black — ultra high contrast)
#  muted:       #6b7280
#  border:      #e5e7eb
#
#  pastel accents (all high-contrast against white):
#    mint:      bg #d1fae5  text #065f46
#    sky:       bg #dbeafe  text #1e3a8a
#    coral:     bg #ffe4e6  text #9f1239
#    violet:    bg #ede9fe  text #4c1d95
#    amber:     bg #fef3c7  text #78350f
#    lime:      bg #ecfccb  text #365314
#
#  primary action: #6366f1 (indigo) — crisp, bold
# ══════════════════════════════════════════════════════════════

STYLE = """
/* ─── BASE ─────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #1a1a2e;
    font-family: 'Outfit', 'Poppins', 'Segoe UI', sans-serif;
    font-size: 13px;
}

/* ─── TOOLBAR ───────────────────────────────────────────── */
QFrame#toolbar {
    background: #6366f1;
    border: none;
    min-height: 60px;
}
QFrame#toolbar QLabel {
    color: #ffffff;
    background: transparent;
}

/* ─── FILTER PANEL ──────────────────────────────────────── */
QFrame#filterPanel {
    background: #f7f8fc;
    border-bottom: 2px solid #e5e7eb;
}

/* ─── INPUTS ────────────────────────────────────────────── */
QLineEdit {
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    color: #1a1a2e;
    padding: 7px 12px;
    font-size: 13px;
    selection-background-color: #c7d2fe;
    selection-color: #1a1a2e;
}
QLineEdit:focus {
    border-color: #6366f1;
    background: #fafafe;
}
QLineEdit::placeholder {
    color: #9ca3af;
}

/* ─── BUTTONS ───────────────────────────────────────────── */
QPushButton {
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    color: #374151;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
    min-width: 80px;
    min-height: 34px;
}
QPushButton:hover {
    border-color: #6366f1;
    color: #6366f1;
    background: #eef2ff;
}
QPushButton:pressed {
    background: #e0e7ff;
    border-color: #4f46e5;
    color: #4f46e5;
}

/* primary / accent */
QPushButton#accentBtn {
    background: #ffffff;
    border: 2px solid #ffffff;
    border-radius: 8px;
    color: #4f46e5;
    font-size: 13px;
    font-weight: 700;
    min-width: 150px;
    min-height: 38px;
    padding: 6px 20px;
}
QPushButton#accentBtn:hover {
    background: #eef2ff;
    border-color: #e0e7ff;
    color: #3730a3;
}
QPushButton#accentBtn:pressed {
    background: #e0e7ff;
    color: #3730a3;
}

/* danger */
QPushButton#dangerBtn {
    color: #dc2626;
    border-color: #fecaca;
    background: #fff5f5;
    min-width: 80px;
}
QPushButton#dangerBtn:hover {
    background: #fee2e2;
    border-color: #f87171;
}

/* toggle buttons — mint when off, indigo when on */
QPushButton#toggleBtn {
    min-width: 48px;
    max-width: 58px;
    min-height: 34px;
    padding: 6px 8px;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0;
    background: #f0fdf4;
    border: 2px solid #bbf7d0;
    color: #15803d;
    border-radius: 8px;
}
QPushButton#toggleBtn:hover {
    background: #dcfce7;
    border-color: #86efac;
}
QPushButton#toggleBtn:checked {
    background: #6366f1;
    border-color: #6366f1;
    color: #ffffff;
}
QPushButton#toggleBtn:checked:hover {
    background: #4f46e5;
    border-color: #4f46e5;
}

/* ─── COMBOBOX ──────────────────────────────────────────── */
QComboBox {
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    color: #1a1a2e;
    padding: 6px 10px;
    font-size: 12px;
    min-width: 120px;
    min-height: 34px;
}
QComboBox:hover { border-color: #6366f1; }
QComboBox:focus { border-color: #6366f1; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 2px solid #c7d2fe;
    border-radius: 8px;
    color: #1a1a2e;
    selection-background-color: #e0e7ff;
    selection-color: #4f46e5;
    outline: none;
    padding: 4px;
}

/* ─── SPINBOX ───────────────────────────────────────────── */
QSpinBox {
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    color: #1a1a2e;
    padding: 5px 8px;
    min-height: 32px;
}
QSpinBox:focus { border-color: #6366f1; }
QSpinBox::up-button, QSpinBox::down-button {
    border: none; background: transparent; width: 16px;
}

/* ─── TREE ──────────────────────────────────────────────── */
QTreeWidget {
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 10px;
    alternate-background-color: #f9fafb;
    show-decoration-selected: 1;
    outline: none;
}
QTreeWidget::item {
    padding: 5px 8px;
    border-radius: 6px;
    margin: 1px 4px;
}
QTreeWidget::item:hover {
    background: #f0f9ff;
}
QTreeWidget::item:selected {
    background: #e0e7ff;
    color: #3730a3;
}
QTreeWidget::item:selected:hover {
    background: #c7d2fe;
}

QHeaderView::section {
    background: #f1f5f9;
    border: none;
    border-bottom: 2px solid #e5e7eb;
    border-right: 1px solid #e5e7eb;
    color: #64748b;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.12em;
    padding: 6px 10px;
    text-transform: uppercase;
}
QHeaderView::section:last { border-right: none; }

/* ─── TEXT EDIT ─────────────────────────────────────────── */
QTextEdit {
    background: #f8fafc;
    border: 2px solid #e5e7eb;
    border-radius: 10px;
    color: #1e293b;
    padding: 10px 12px;
    font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
    font-size: 11.5px;
    selection-background-color: #c7d2fe;
    selection-color: #1a1a2e;
}

/* ─── SPLITTER ──────────────────────────────────────────── */
QSplitter { background: #ffffff; }
QSplitter::handle { background: #e5e7eb; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical   { height: 2px; }
QSplitter::handle:hover { background: #6366f1; }

/* ─── SCROLLBARS ────────────────────────────────────────── */
QScrollBar:vertical {
    background: #f1f5f9;
    width: 8px;
    border-radius: 4px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 28px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background: #6366f1; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #f1f5f9;
    height: 8px;
    border-radius: 4px;
    margin: 2px 4px;
}
QScrollBar::handle:horizontal {
    background: #cbd5e1;
    min-width: 28px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover { background: #6366f1; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ─── STATUS BAR ────────────────────────────────────────── */
QStatusBar {
    background: #f1f5f9;
    border-top: 1px solid #e5e7eb;
    color: #64748b;
    font-size: 11px;
    padding: 2px 10px;
}
QStatusBar::item { border: none; }

/* ─── PROGRESS BAR ──────────────────────────────────────── */
QProgressBar {
    background: #e5e7eb;
    border: none;
    border-radius: 2px;
    height: 4px;
    max-height: 4px;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #6366f1, stop:0.5 #a78bfa, stop:1 #38bdf8);
    border-radius: 2px;
}

/* ─── MENU ──────────────────────────────────────────────── */
QMenu {
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 10px;
    color: #1a1a2e;
    padding: 5px;
}
QMenu::item {
    padding: 7px 20px 7px 12px;
    border-radius: 6px;
    font-size: 12px;
}
QMenu::item:selected {
    background: #e0e7ff;
    color: #4f46e5;
}
QMenu::separator { height: 1px; background: #e5e7eb; margin: 4px 0; }

/* ─── LABELS ────────────────────────────────────────────── */
QLabel#appTitle {
    font-size: 18px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.02em;
}
QLabel#appSubtitle {
    font-size: 11px;
    color: #c7d2fe;
    letter-spacing: 0.04em;
}
QLabel#sectionLabel {
    color: #6b7280;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.14em;
}
QLabel#statAccent {
    color: #6366f1;
    font-size: 11px;
    font-weight: 700;
}
QLabel#statMuted {
    color: #9ca3af;
    font-size: 11px;
}
QLabel#folderLabel {
    color: #e0e7ff;
    font-size: 12px;
}

/* ─── COLORED SECTION TAGS ──────────────────────────────── */
QLabel#tagMint {
    background: #d1fae5;
    color: #065f46;
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.1em;
}
QLabel#tagSky {
    background: #dbeafe;
    color: #1e40af;
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.1em;
}
"""


# ══════════════════════════════════════════════════════════════
#  SEARCH WORKER
# ══════════════════════════════════════════════════════════════
class SearchWorker(QThread):
    result_ready = Signal(list)
    progress     = Signal(int)
    status_msg   = Signal(str)
    finished     = Signal(int, float)

    def __init__(self, config):
        super().__init__()
        from PySide6.QtWidgets import QStyle
        # inside __init__, after super().__init__():
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        self.config = config
        self._abort = False

    def abort(self): self._abort = True

    def run(self):
        t0 = datetime.now()
        c  = self.config
        results = []

        regex_obj = None
        if c["regex"] and c["query"]:
            flags = 0 if c["case_sensitive"] else re.IGNORECASE
            try:
                regex_obj = re.compile(c["query"], flags)
            except re.error:
                self.status_msg.emit("Invalid regex pattern")
                self.finished.emit(0, 0.0)
                return

        q_cmp = c["query"] if c["case_sensitive"] else c["query"].lower()

        all_files = []
        try:
            for root, dirs, files in os.walk(c["folder"]):
                if self._abort: break
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    all_files.append((root, f, os.path.join(root, f)))
        except PermissionError:
            pass

        total = len(all_files)
        self.status_msg.emit(f"Scanning {total:,} files...")

        TEXT_EXTS = {
            ".txt",".py",".js",".ts",".jsx",".tsx",".html",".htm",".css",
            ".scss",".json",".xml",".yaml",".yml",".md",".rst",".toml",
            ".ini",".cfg",".conf",".sh",".bash",".zsh",".c",".cpp",".h",
            ".hpp",".java",".kt",".go",".rs",".rb",".php",".swift",".r",
            ".sql",".log",".csv",".env",".tf",".ipynb",".lua",".dart",
            ".vue",".svelte",".fish",".ps1",".bat",".cmd",
        }

        for i, (root, f, full_path) in enumerate(all_files):
            if self._abort: break
            if i % 300 == 0:
                self.progress.emit(int(i / max(total, 1) * 100))

            if c["types"] and not any(f.lower().endswith(t.lower()) for t in c["types"]):
                continue
            try:
                stat = os.stat(full_path)
            except (PermissionError, FileNotFoundError):
                continue

            file_size = stat.st_size
            mtime     = datetime.fromtimestamp(stat.st_mtime)

            if c["min_size"] and file_size < c["min_size"] * 1024: continue
            if c["max_size"] and file_size > c["max_size"] * 1024: continue
            if c["start_dt"] and mtime < c["start_dt"]: continue
            if c["end_dt"]   and mtime > c["end_dt"]:   continue

            f_cmp = f if c["case_sensitive"] else f.lower()
            name_matched    = False
            name_score      = 0
            content_matches = []

            if not c["query"]:
                name_matched = True; name_score = 100
            elif regex_obj:
                if regex_obj.search(f): name_matched = True; name_score = 100
            elif c["fuzzy"] and FUZZY_AVAILABLE:
                name_score = fuzz.partial_ratio(q_cmp, f_cmp)
                if name_score >= c["fuzzy_threshold"]: name_matched = True
            else:
                if q_cmp in f_cmp: name_matched = True; name_score = 100

            if c["search_content"] and c["query"] and not name_matched:
                ext = Path(f).suffix.lower()
                if ext in TEXT_EXTS and file_size < 5 * 1024 * 1024:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        if regex_obj:
                            for m in regex_obj.finditer(content):
                                s = max(0, m.start()-60); e = min(len(content), m.end()+60)
                                content_matches.append(content[s:e].replace("\n"," ").strip())
                                if len(content_matches) >= 3: break
                        else:
                            cc  = content if c["case_sensitive"] else content.lower()
                            idx = 0
                            while len(content_matches) < 3:
                                pos = cc.find(q_cmp, idx)
                                if pos == -1: break
                                s = max(0, pos-60); e = min(len(content), pos+60+len(c["query"]))
                                content_matches.append(content[s:e].replace("\n"," ").strip())
                                idx = pos + 1
                    except Exception:
                        pass

            if not name_matched and not content_matches: continue

            results.append({
                "name":            f,
                "full_path":       full_path,
                "rel_path":        os.path.relpath(full_path, c["folder"]),
                "folder":          root,
                "size":            file_size,
                "mtime":           mtime,
                "score":           name_score,
                "name_matched":    name_matched,
                "content_matches": content_matches,
                "ext":             Path(f).suffix.lower(),
            })
            if len(results) >= c["max_results"]: break

        s = c["sort_by"]
        if   s == "Name":      results.sort(key=lambda x: x["name"].lower())
        elif s == "Date":      results.sort(key=lambda x: x["mtime"], reverse=True)
        elif s == "Size":      results.sort(key=lambda x: x["size"],  reverse=True)
        elif s == "Relevance": results.sort(key=lambda x: x["score"], reverse=True)
        elif s == "Extension": results.sort(key=lambda x: (x["ext"], x["name"].lower()))

        elapsed = (datetime.now() - t0).total_seconds()
        self.result_ready.emit(results)
        self.finished.emit(len(results), elapsed)


# ══════════════════════════════════════════════════════════════
#  MATCH HIGHLIGHTER
# ══════════════════════════════════════════════════════════════
class MatchHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, query, case_sensitive=False, is_regex=False):
        super().__init__(doc)
        self.query = query; self.case_sensitive = case_sensitive; self.is_regex = is_regex
        self.fmt = QTextCharFormat()
        self.fmt.setBackground(QColor("#fde68a"))
        self.fmt.setForeground(QColor("#78350f"))

    def highlightBlock(self, text):
        if not self.query: return
        if self.is_regex:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            try:
                for m in re.finditer(self.query, text, flags):
                    self.setFormat(m.start(), m.end()-m.start(), self.fmt)
            except: pass
        else:
            t = text if self.case_sensitive else text.lower()
            q = self.query if self.case_sensitive else self.query.lower()
            idx = 0
            while True:
                pos = t.find(q, idx)
                if pos == -1: break
                self.setFormat(pos, len(q), self.fmt)
                idx = pos + 1


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════
EXT_COLORS = {
    ".py":"#2563eb",   ".ipynb":"#7c3aed",
    ".js":"#d97706",   ".ts":"#1d4ed8",  ".jsx":"#0891b2", ".tsx":"#0891b2",
    ".html":"#dc2626", ".css":"#2563eb", ".scss":"#9333ea",
    ".json":"#16a34a", ".yaml":"#7c3aed",".yml":"#7c3aed",
    ".md":"#4f46e5",   ".rs":"#ea580c",  ".go":"#0891b2",
    ".java":"#ca8a04", ".kt":"#7c3aed",  ".rb":"#dc2626",
    ".sh":"#16a34a",   ".bash":"#16a34a",
    ".txt":"#64748b",  ".log":"#64748b",
    ".sql":"#b45309",  ".csv":"#15803d",
    ".c":"#4338ca",    ".cpp":"#4338ca",
    ".png":"#db2777",  ".jpg":"#db2777",  ".jpeg":"#db2777",
    ".svg":"#ea580c",  ".pdf":"#dc2626",
    ".zip":"#854d0e",  ".tar":"#854d0e",
}
def ext_color(ext): return EXT_COLORS.get(ext, "#64748b")

def fmt_size(b):
    if b < 1024:  return f"{b} B"
    if b < 1<<20: return f"{b/1024:.1f} KB"
    if b < 1<<30: return f"{b/1048576:.1f} MB"
    return f"{b/1073741824:.1f} GB"


# ══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════
class QuickSearch(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finder+")
        self.setMinimumSize(1050, 680)
        self.resize(1300, 820)
        self.folder_path      = ""
        self._worker          = None
        self._current_results = []
        self._search_timer    = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(320)
        self._search_timer.timeout.connect(self.run_search)
        self.init_ui()
        self.setup_shortcuts()

    # ── UI ────────────────────────────────────────────────────
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_filter_panel())

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        root.addWidget(self.progress_bar)

        body = QWidget()
        body.setStyleSheet("background:#ffffff;")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(12, 12, 12, 12)
        body_lay.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.addWidget(self._build_results_panel())
        splitter.addWidget(self._build_preview_panel())
        splitter.setSizes([740, 500])
        body_lay.addWidget(splitter)
        root.addWidget(body, stretch=1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._lbl_folder = QLabel("No folder selected")
        self._lbl_folder.setObjectName("statMuted")
        self._lbl_count  = QLabel("")
        self._lbl_count.setObjectName("statAccent")
        self._lbl_time   = QLabel("")
        self._lbl_time.setObjectName("statMuted")
        self.status_bar.addWidget(self._lbl_folder)
        self.status_bar.addPermanentWidget(self._lbl_count)
        self.status_bar.addPermanentWidget(self._lbl_time)

    def _build_toolbar(self):
        bar = QFrame()
        bar.setObjectName("toolbar")
        bar.setMinimumHeight(60)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 8, 20, 8)
        lay.setSpacing(14)

        # title
        title = QLabel("Finder+")
        title.setStyleSheet(
            "color: #ffffff; font-size: 22px; font-weight: 800; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        title.setMinimumWidth(120)
        lay.addWidget(title)

        lay.addWidget(self._vsep("#818cf8"))

        # folder display
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet(
            "color: #c7d2fe; font-size: 12px; background: transparent; border: none;"
        )
        self.folder_label.setMaximumWidth(480)
        lay.addWidget(self.folder_label)

        # Select Folder — ghost/outline style that belongs on the indigo bar
        folder_btn = QPushButton("Select Folder")
        folder_btn.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: 2px solid #a5b4fc;"
            "  border-radius: 8px;"
            "  color: #e0e7ff;"
            "  font-size: 13px;"
            "  font-weight: 700;"
            "  min-width: 140px;"
            "  min-height: 36px;"
            "  padding: 6px 20px;"
            "}"
            "QPushButton:hover {"
            "  background: #4f46e5;"
            "  border-color: #c7d2fe;"
            "  color: #ffffff;"
            "}"
            "QPushButton:pressed {"
            "  background: #3730a3;"
            "  border-color: #818cf8;"
            "}"
        )
        folder_btn.clicked.connect(self.select_folder)
        lay.addWidget(folder_btn)

        lay.addStretch()

        # Export — soft indigo pill
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(
            "QPushButton {"
            "  background: rgba(255,255,255,0.15);"
            "  border: 2px solid rgba(255,255,255,0.35);"
            "  border-radius: 8px;"
            "  color: #e0e7ff;"
            "  font-size: 12px;"
            "  font-weight: 700;"
            "  min-width: 82px;"
            "  min-height: 34px;"
            "  padding: 6px 14px;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(255,255,255,0.25);"
            "  border-color: rgba(255,255,255,0.6);"
            "  color: #ffffff;"
            "}"
            "QPushButton:pressed { background: rgba(255,255,255,0.1); }"
        )
        export_btn.clicked.connect(self.export_results)
        lay.addWidget(export_btn)

        # Clear — soft red pill that still feels at home on indigo
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(
            "QPushButton {"
            "  background: rgba(254,202,202,0.2);"
            "  border: 2px solid rgba(252,165,165,0.5);"
            "  border-radius: 8px;"
            "  color: #fecaca;"
            "  font-size: 12px;"
            "  font-weight: 700;"
            "  min-width: 72px;"
            "  min-height: 34px;"
            "  padding: 6px 12px;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(239,68,68,0.3);"
            "  border-color: #fca5a5;"
            "  color: #ffffff;"
            "}"
            "QPushButton:pressed { background: rgba(239,68,68,0.5); }"
        )
        clear_btn.clicked.connect(self.clear_all)
        lay.addWidget(clear_btn)

        return bar

    def _build_filter_panel(self):
        panel = QFrame()
        panel.setObjectName("filterPanel")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(16, 10, 16, 10)
        outer.setSpacing(8)

        # ── Row 1: search + mode toggles ──
        r1 = QHBoxLayout(); r1.setSpacing(8)

        tag1 = QLabel("SEARCH")
        tag1.setStyleSheet(
            "background: #6366f1; color: #ffffff; border-radius: 6px;"
            "padding: 4px 10px; font-size: 10px; font-weight: 800; letter-spacing: 0.1em;"
        )
        tag1.setFixedHeight(28)
        r1.addWidget(tag1)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Type to search filenames or file contents...")
        self.search_bar.setMinimumHeight(36)
        self.search_bar.textChanged.connect(self._trigger)
        r1.addWidget(self.search_bar)

        def tbtn(text, tip, sc=""):
            b = QPushButton(text)
            b.setObjectName("toggleBtn")
            b.setCheckable(True)
            b.setToolTip(f"{tip}  {sc}".strip())
            b.toggled.connect(self._trigger)
            return b

        self.btn_regex   = tbtn(".*",  "Regex mode",            "Ctrl+R")
        self.btn_case    = tbtn("Aa",  "Case sensitive",         "Ctrl+Shift+C")
        self.btn_fuzzy   = tbtn("~",   "Fuzzy match",            "Ctrl+F")
        self.btn_content = tbtn("[ ]", "Search inside files",    "Ctrl+Shift+F")

        if not FUZZY_AVAILABLE:
            self.btn_fuzzy.setEnabled(False)
            self.btn_fuzzy.setToolTip("pip install rapidfuzz to enable fuzzy matching")

        for b in (self.btn_regex, self.btn_case, self.btn_fuzzy, self.btn_content):
            r1.addWidget(b)
        outer.addLayout(r1)

        # ── Row 2: filters ──
        r2 = QHBoxLayout(); r2.setSpacing(8)

        tag2 = QLabel("FILTERS")
        tag2.setStyleSheet(
            "background: #06b6d4; color: #ffffff; border-radius: 6px;"
            "padding: 4px 10px; font-size: 10px; font-weight: 800; letter-spacing: 0.1em;"
        )
        tag2.setFixedHeight(28)
        r2.addWidget(tag2)

        self.type_filter = QLineEdit()
        self.type_filter.setPlaceholderText("Extensions: .py .js .txt")
        self.type_filter.setMaximumWidth(200)
        self.type_filter.setMinimumHeight(32)
        self.type_filter.textChanged.connect(self._trigger)
        r2.addWidget(self.type_filter)

        r2.addWidget(self._vsep())

        self.start_date = QLineEdit()
        self.start_date.setPlaceholderText("From YYYY-MM-DD")
        self.start_date.setMaximumWidth(138)
        self.start_date.setMinimumHeight(32)
        self.start_date.textChanged.connect(self._trigger)
        r2.addWidget(self.start_date)

        self.end_date = QLineEdit()
        self.end_date.setPlaceholderText("To YYYY-MM-DD")
        self.end_date.setMaximumWidth(138)
        self.end_date.setMinimumHeight(32)
        self.end_date.textChanged.connect(self._trigger)
        r2.addWidget(self.end_date)

        r2.addWidget(self._vsep())

        for ltext in ["SIZE KB"]:
            lbl = QLabel(ltext); lbl.setObjectName("sectionLabel"); r2.addWidget(lbl)

        self.min_size = QSpinBox()
        self.min_size.setRange(0, 1_000_000); self.min_size.setSpecialValueText("min")
        self.min_size.setMaximumWidth(78); self.min_size.setMinimumHeight(32)
        self.min_size.valueChanged.connect(self._trigger)
        r2.addWidget(self.min_size)

        dash = QLabel("—"); dash.setObjectName("sectionLabel"); r2.addWidget(dash)

        self.max_size = QSpinBox()
        self.max_size.setRange(0, 1_000_000); self.max_size.setSpecialValueText("max")
        self.max_size.setMaximumWidth(78); self.max_size.setMinimumHeight(32)
        self.max_size.valueChanged.connect(self._trigger)
        r2.addWidget(self.max_size)

        r2.addWidget(self._vsep())

        sort_lbl = QLabel("SORT"); sort_lbl.setObjectName("sectionLabel"); r2.addWidget(sort_lbl)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Relevance","Name","Date","Size","Extension"])
        self.sort_combo.setMinimumHeight(32)
        self.sort_combo.currentTextChanged.connect(self._trigger)
        r2.addWidget(self.sort_combo)

        r2.addWidget(self._vsep())

        max_lbl = QLabel("MAX"); max_lbl.setObjectName("sectionLabel"); r2.addWidget(max_lbl)
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(10, 100_000); self.max_results_spin.setValue(5000)
        self.max_results_spin.setSingleStep(500); self.max_results_spin.setMaximumWidth(82)
        self.max_results_spin.setMinimumHeight(32)
        self.max_results_spin.valueChanged.connect(self._trigger)
        r2.addWidget(self.max_results_spin)

        self.fuzzy_thr_lbl = QLabel("THRESHOLD"); self.fuzzy_thr_lbl.setObjectName("sectionLabel")
        self.fuzzy_thr_lbl.hide(); r2.addWidget(self.fuzzy_thr_lbl)

        self.fuzzy_threshold = QSpinBox()
        self.fuzzy_threshold.setRange(0,100); self.fuzzy_threshold.setValue(60)
        self.fuzzy_threshold.setMaximumWidth(68); self.fuzzy_threshold.setMinimumHeight(32)
        self.fuzzy_threshold.hide(); self.fuzzy_threshold.valueChanged.connect(self._trigger)
        r2.addWidget(self.fuzzy_threshold)
        self.btn_fuzzy.toggled.connect(lambda v:(
            self.fuzzy_thr_lbl.setVisible(v), self.fuzzy_threshold.setVisible(v)))

        r2.addStretch()

        self.group_btn = QPushButton("Group by folder")
        self.group_btn.setCheckable(True)
        self.group_btn.setMinimumHeight(32)
        self.group_btn.toggled.connect(lambda _: self._populate_tree(self._current_results))
        r2.addWidget(self.group_btn)

        outer.addLayout(r2)
        return panel

    def _build_results_panel(self):
        wrap = QWidget()
        wrap.setStyleSheet("QWidget { background: #ffffff; }")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        hdr = QHBoxLayout()
        res_lbl = QLabel("RESULTS")
        res_lbl.setStyleSheet(
            "color: #6366f1; font-size: 10px; font-weight: 800; letter-spacing: 0.15em;"
        )
        hdr.addWidget(res_lbl); hdr.addStretch()
        lay.addLayout(hdr)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Name", "Path", "Size", "Modified"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setRootIsDecorated(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tree.header().setSectionResizeMode(3, QHeaderView.Fixed)
        self.tree.header().resizeSection(0, 240)
        self.tree.header().resizeSection(2, 78)
        self.tree.header().resizeSection(3, 94)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.tree.currentItemChanged.connect(self._on_select)
        self.tree.itemActivated.connect(self._open_item)
        lay.addWidget(self.tree)
        return wrap

    def _build_preview_panel(self):
        wrap = QWidget()
        wrap.setStyleSheet("QWidget { background: #ffffff; }")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        prev_lbl = QLabel("PREVIEW")
        prev_lbl.setStyleSheet(
            "color: #06b6d4; font-size: 10px; font-weight: 800; letter-spacing: 0.15em;"
        )
        hdr.addWidget(prev_lbl); hdr.addStretch()
        self.preview_path_lbl = QLabel("")
        self.preview_path_lbl.setObjectName("statMuted")
        self.preview_path_lbl.setMaximumWidth(300)
        hdr.addWidget(self.preview_path_lbl)
        lay.addLayout(hdr)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setLineWrapMode(QTextEdit.NoWrap)
        lay.addWidget(self.preview)
        self._highlighter = None
        return wrap

    # ── HELPERS ───────────────────────────────────────────────
    def _vsep(self, color="#e5e7eb"):
        s = QFrame(); s.setFrameShape(QFrame.VLine)
        s.setStyleSheet(f"color: {color};"); s.setFixedHeight(22)
        return s

    # ── SHORTCUTS ─────────────────────────────────────────────
    def setup_shortcuts(self):
        for key, fn in [
            ("Ctrl+R",       lambda: self.btn_regex.setChecked(not self.btn_regex.isChecked())),
            ("Ctrl+F",       lambda: self.btn_fuzzy.setChecked(not self.btn_fuzzy.isChecked())),
            ("Ctrl+Shift+F", lambda: self.btn_content.setChecked(not self.btn_content.isChecked())),
            ("Ctrl+Shift+C", lambda: self.btn_case.setChecked(not self.btn_case.isChecked())),
            ("Ctrl+L",       self.search_bar.setFocus),
            ("Escape",       self.abort_search),
            ("Ctrl+E",       self.export_results),
            ("Ctrl+O",       self.select_folder),
        ]:
            a = QAction(self); a.setShortcut(QKeySequence(key))
            a.triggered.connect(fn); self.addAction(a)

    # ── EVENTS ────────────────────────────────────────────────
    def _trigger(self): self._search_timer.start()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            display = folder if len(folder) < 65 else "..." + folder[-62:]
            self.folder_label.setText(display)
            self._lbl_folder.setText(display)
            self.run_search()

    def abort_search(self):
        if self._worker and self._worker.isRunning():
            self._worker.abort(); self.progress_bar.hide()
            self.status_bar.showMessage("Cancelled", 2000)

    def clear_all(self):
        for w in (self.search_bar, self.type_filter, self.start_date, self.end_date):
            w.clear()
        self.tree.clear(); self.preview.clear()
        self.preview_path_lbl.setText("")
        self._current_results = []
        self._lbl_count.setText(""); self._lbl_time.setText("")

    # ── SEARCH ────────────────────────────────────────────────
    def run_search(self):
        if not self.folder_path: return
        self.abort_search()
        types = [t.strip() for t in self.type_filter.text().replace(","," ").split() if t.strip()]
        s, e  = self.start_date.text().strip(), self.end_date.text().strip()
        try:
            start_dt = datetime.strptime(s, "%Y-%m-%d") if s else None
            end_dt   = datetime.strptime(e, "%Y-%m-%d") if e else None
        except ValueError:
            self.status_bar.showMessage("Invalid date — use YYYY-MM-DD", 3000); return

        config = dict(
            folder=self.folder_path, query=self.search_bar.text(),
            types=types, start_dt=start_dt, end_dt=end_dt,
            fuzzy=self.btn_fuzzy.isChecked(), fuzzy_threshold=self.fuzzy_threshold.value(),
            regex=self.btn_regex.isChecked(), case_sensitive=self.btn_case.isChecked(),
            search_content=self.btn_content.isChecked(),
            min_size=self.min_size.value() or None, max_size=self.max_size.value() or None,
            sort_by=self.sort_combo.currentText(), max_results=self.max_results_spin.value(),
        )
        self._worker = SearchWorker(config)
        self._worker.result_ready.connect(self._on_results)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.status_msg.connect(self.status_bar.showMessage)
        self._worker.finished.connect(self._on_done)
        self.progress_bar.setValue(0); self.progress_bar.show()
        self.status_bar.showMessage("Searching...")
        self._worker.start()

    def _on_results(self, results):
        self._current_results = results
        self._populate_tree(results)

    def _populate_tree(self, results):
        self.tree.clear()
        if not results: return
        if self.group_btn.isChecked():
            folders = {}
            for r in results: folders.setdefault(r["folder"],[]).append(r)
            for folder, items in sorted(folders.items()):
                rel = os.path.relpath(folder, self.folder_path)
                p   = QTreeWidgetItem(self.tree, [rel, "", f"{len(items)} files", ""])
                p.setForeground(0, QColor("#94a3b8"))
                for r in items: self._add_row(p, r)
                p.setExpanded(True)
        else:
            for r in results: self._add_row(self.tree, r)

    def _add_row(self, parent, r):
        item = QTreeWidgetItem([
            r["name"], r["rel_path"], fmt_size(r["size"]),
            r["mtime"].strftime("%Y-%m-%d")
        ])
        item.setData(0, Qt.UserRole, r["full_path"])
        item.setForeground(0, QColor(ext_color(r["ext"])))
        item.setForeground(1, QColor("#94a3b8"))
        item.setForeground(2, QColor("#64748b"))
        item.setForeground(3, QColor("#64748b"))
        if r["content_matches"]:
            item.setForeground(1, QColor("#16a34a"))
            item.setToolTip(1, "Content match: " + r["content_matches"][0][:120])
        if isinstance(parent, QTreeWidget): parent.addTopLevelItem(item)
        else: parent.addChild(item)

    def _on_done(self, count, elapsed):
        self.progress_bar.hide()
        self._lbl_count.setText(f"{count:,} results")
        self._lbl_time.setText(f"  {elapsed:.2f}s")
        self.status_bar.showMessage(f"Found {count:,} results in {elapsed:.2f}s", 5000)

    # ── PREVIEW ───────────────────────────────────────────────
    def _on_select(self, current, _):
        if not current: return
        path = current.data(0, Qt.UserRole)
        if path and os.path.isfile(path): self._load_preview(path)

    def _load_preview(self, path):
        self.preview_path_lbl.setText(os.path.basename(path))
        ext = Path(path).suffix.lower()
        TEXT_EXTS = {
            ".txt",".py",".js",".ts",".jsx",".tsx",".html",".htm",".css",
            ".scss",".json",".xml",".yaml",".yml",".md",".rst",".toml",
            ".ini",".cfg",".sh",".bash",".c",".cpp",".h",".java",".kt",
            ".go",".rs",".rb",".php",".swift",".sql",".log",".csv",".env",
            ".lua",".dart",".vue",".svelte",".ipynb",".tf",
        }
        if ext not in TEXT_EXTS:
            self.preview.setPlainText(f"[No preview available for {ext} files]"); return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(500_000)
            if os.path.getsize(path) > 500_000:
                content += "\n\n[... truncated at 500 KB ...]"
            self.preview.setPlainText(content)
            self._highlighter = MatchHighlighter(
                self.preview.document(), self.search_bar.text(),
                self.btn_case.isChecked(), self.btn_regex.isChecked()
            )
            q = self.search_bar.text()
            if q:
                cur = self.preview.document().find(q)
                if cur and not cur.isNull():
                    self.preview.setTextCursor(cur)
                    self.preview.ensureCursorVisible()
        except Exception as ex:
            self.preview.setPlainText(f"[Error reading file: {ex}]")

    # ── CONTEXT MENU ──────────────────────────────────────────
    def _context_menu(self, pos):
        items = self.tree.selectedItems()
        if not items: return
        menu   = QMenu(self)
        a_open = menu.addAction("Open file")
        a_dir  = menu.addAction("Open containing folder")
        menu.addSeparator()
        a_cp   = menu.addAction("Copy path")
        a_cn   = menu.addAction("Copy filename")
        a_ca   = menu.addAction(f"Copy all paths  ({len(items)})")
        act    = menu.exec(QCursor.pos())
        paths  = [i.data(0, Qt.UserRole) for i in items if i.data(0, Qt.UserRole)]
        if not paths: return
        if   act == a_open: [QDesktopServices.openUrl(QUrl.fromLocalFile(p)) for p in paths[:5] if os.path.isfile(p)]
        elif act == a_dir:  [QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(p))) for p in paths[:5]]
        elif act == a_cp:   QApplication.clipboard().setText(paths[0])
        elif act == a_cn:   QApplication.clipboard().setText(os.path.basename(paths[0]))
        elif act == a_ca:   QApplication.clipboard().setText("\n".join(paths))

    def _open_item(self, item, _):
        path = item.data(0, Qt.UserRole)
        if path and os.path.isfile(path): QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    # ── EXPORT ────────────────────────────────────────────────
    def export_results(self):
        if not self._current_results:
            self.status_bar.showMessage("Nothing to export", 2000); return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "results.txt",
            "Text Files (*.txt);;CSV Files (*.csv)"
        )
        if not save_path: return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                if save_path.endswith(".csv"):
                    f.write("Name,Path,Size,Modified,Extension\n")
                    for r in self._current_results:
                        f.write(f'"{r["name"]}","{r["full_path"]}",{r["size"]},{r["mtime"]:%Y-%m-%d},{r["ext"]}\n')
                else:
                    f.write(f"QuickSearch Export — {datetime.now():%Y-%m-%d %H:%M:%S}\n")
                    f.write(f"Folder : {self.folder_path}\nQuery  : {self.search_bar.text()}\n")
                    f.write(f"Results: {len(self._current_results)}\n{'─'*80}\n\n")
                    for r in self._current_results: f.write(r["full_path"] + "\n")
            self.status_bar.showMessage(f"Exported to {save_path}", 3000)
        except Exception as ex:
            self.status_bar.showMessage(f"Export failed: {ex}", 4000)


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)

    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor("#ffffff"))
    pal.setColor(QPalette.WindowText,      QColor("#1a1a2e"))
    pal.setColor(QPalette.Base,            QColor("#ffffff"))
    pal.setColor(QPalette.AlternateBase,   QColor("#f9fafb"))
    pal.setColor(QPalette.ToolTipBase,     QColor("#ffffff"))
    pal.setColor(QPalette.ToolTipText,     QColor("#1a1a2e"))
    pal.setColor(QPalette.Text,            QColor("#1a1a2e"))
    pal.setColor(QPalette.Button,          QColor("#ffffff"))
    pal.setColor(QPalette.ButtonText,      QColor("#374151"))
    pal.setColor(QPalette.BrightText,      QColor("#6366f1"))
    pal.setColor(QPalette.Highlight,       QColor("#e0e7ff"))
    pal.setColor(QPalette.HighlightedText, QColor("#3730a3"))
    pal.setColor(QPalette.Light,           QColor("#f9fafb"))
    pal.setColor(QPalette.Mid,             QColor("#e5e7eb"))
    pal.setColor(QPalette.Dark,            QColor("#d1d5db"))
    pal.setColor(QPalette.Shadow,          QColor("#9ca3af"))
    app.setPalette(pal)

    window = QuickSearch()
    window.show()
    sys.exit(app.exec())
