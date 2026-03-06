import os
import csv
import hashlib
from pathlib import Path

# ---- Config ----
REPO_ROOT = Path(".").resolve()
OUT_DIR = REPO_ROOT / "docs" / "repo_inventory"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEXT_EXTS = {
    ".md", ".txt", ".yaml", ".yml", ".json", ".py", ".ps1", ".sql",
    ".js", ".ts", ".tsx", ".html", ".css", ".xml", ".csv"
}

SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}

# ---- Helpers ----
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTS

def safe_read_text(path: Path) -> str:
    # Handle BOM + Windows oddities
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return ""

def count_lines_chars(path: Path) -> tuple[int, int]:
    if not is_text_file(path):
        return (0, 0)
    text = safe_read_text(path)
    if not text:
        return (0, 0)
    return (text.count("\n") + 1, len(text))

def walk_repo(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # prune dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        pdir = Path(dirpath)

        for fn in filenames:
            yield pdir / fn

def classify_path(rel: str) -> str:
    rel_l = rel.replace("\\", "/").lower()
    if rel_l.startswith("contract/v1/acceptance/"):
        return "SPINE: validation + governance"
    if rel_l.startswith("contract/v1/policy/"):
        return "SPINE: roles/lanes/policy controls"
    if rel_l.startswith("contract/v1/tools/"):
        return "SPINE: tool gateway + registry"
    if rel_l.startswith("contract/v1/harness/"):
        return "SPINE: deterministic test harness + fixtures"
    if rel_l.startswith("contract/v1/orchestration/"):
        return "SPINE: orchestrator contract / determinism"
    if rel_l.startswith("contract/v1/data/"):
        return "SPINE: data model + DDL"
    if rel_l.startswith("contract/v1/agents/"):
        return "BRAIN: agent contracts"
    if rel_l.startswith("contract/v1/programs/"):
        return "BRAIN: deterministic program contracts"
    if rel_l.startswith("contract/v1/knowledge/"):
        return "BRAIN: knowledge contracts + authority catalogs"
    if rel_l.startswith("contract/v1/taxonomies/"):
        return "BRAIN: taxonomies (tags/entities/coa/pattern packs)"
    if rel_l.startswith("contract/v1/schemas/"):
        return "SPINE/BRAIN: canonical schemas (SSOT)"
    if rel_l.startswith("contract/v1/runner/"):
        return "BRAIN: runnable engines (local execution)"
    if rel_l.startswith("docs/"):
        return "HUMAN: documentation + attorney narratives"
    return "OTHER"

def summarize_folder_metrics(rows):
    # Folder metrics: total bytes + file counts by top-level folder
    agg = {}
    for r in rows:
        rel = r["path"]
        top = rel.split("/")[0] if "/" in rel else rel
        agg.setdefault(top, {"files": 0, "bytes": 0})
        agg[top]["files"] += 1
        agg[top]["bytes"] += int(r["bytes"])
    return agg

def build_tree(paths):
    # Build a simple ASCII tree for all paths
    # Group by directory
    dirs = {}
    for p in paths:
        parts = p.split("/")
        for i in range(1, len(parts)):
            parent = "/".join(parts[:i])
            child = parts[i]
            dirs.setdefault(parent, set()).add(child)
        dirs.setdefault("", set()).add(parts[0])

    def render(node, prefix=""):
        children = sorted(dirs.get(node, []))
        lines = []
        for i, c in enumerate(children):
            is_last = i == len(children) - 1
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + c)
            child_key = (node + "/" + c).strip("/")
            # if child has children, render deeper
            if child_key in dirs:
                extension = "    " if is_last else "│   "
                lines.extend(render(child_key, prefix + extension))
        return lines

    return "\n".join(render(""))

def main():
    rows = []
    all_paths = []

    for p in walk_repo(REPO_ROOT):
        if not p.is_file():
            continue
        rel = p.relative_to(REPO_ROOT).as_posix()
        # skip inventory outputs to avoid recursion noise
        if rel.startswith("docs/repo_inventory/"):
            continue

        all_paths.append(rel)

        size = p.stat().st_size
        sha = sha256_file(p)

        lines, chars = count_lines_chars(p)

        rows.append({
            "path": rel,
            "bytes": size,
            "lines": lines,
            "chars": chars,
            "sha256": sha,
            "classification": classify_path(rel),
        })

    # Write metrics CSV
    csv_path = OUT_DIR / "repo_metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        w.writeheader()
        for r in sorted(rows, key=lambda x: x["path"]):
            w.writerow(r)

    # Write tree
    tree_md = OUT_DIR / "repo_tree.md"
    tree_text = build_tree(sorted(all_paths))
    tree_md.write_text(f"# Repo Tree (AI Legal Service)\n\n```\n{tree_text}\n```\n", encoding="utf-8")

    # Folder summary
    folder_summary = summarize_folder_metrics(rows)
    folder_md = OUT_DIR / "folder_summary.md"
    lines_out = ["# Folder Summary\n", "| Folder | Files | Bytes |", "|---|---:|---:|"]
    for k in sorted(folder_summary.keys()):
        lines_out.append(f"| {k} | {folder_summary[k]['files']} | {folder_summary[k]['bytes']} |")
    folder_md.write_text("\n".join(lines_out) + "\n", encoding="utf-8")

    # Catalog scaffold (descriptions to be filled/augmented by you + me)
    catalog_md = OUT_DIR / "repo_catalog.md"
    catalog_lines = [
        "# Repo Catalog (What it is / How it connects / Why it matters)\n",
        "This file is generated. Edit freely.\n",
        "## Legend\n",
        "- **SPINE**: deterministic governance + SSOT + validation + tool gating\n",
        "- **BRAIN**: legal reasoning modules (agents/programs/knowledge/pattern packs)\n",
        "- **HUMAN**: attorney-facing and developer documentation\n",
    ]

    for r in sorted(rows, key=lambda x: x["path"]):
        catalog_lines.append(f"\n---\n## `{r['path']}`\n")
        catalog_lines.append(f"- **Classification:** {r['classification']}\n")
        catalog_lines.append(f"- **Metrics:** {r['bytes']} bytes | {r['lines']} lines | {r['chars']} chars\n")
        catalog_lines.append(f"- **SHA-256:** `{r['sha256']}`\n")
        catalog_lines.append("### What’s in this file\n- _TODO: Fill summary_\n")
        catalog_lines.append("### How it connects to the platform\n- _TODO: Describe upstream/downstream dependencies_\n")
        catalog_lines.append("### Why it matters\n- _TODO: Explain value/risk if wrong_\n")

    catalog_md.write_text("\n".join(catalog_lines), encoding="utf-8")

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {tree_md}")
    print(f"Wrote: {folder_md}")
    print(f"Wrote: {catalog_md}")

if __name__ == "__main__":
    main()