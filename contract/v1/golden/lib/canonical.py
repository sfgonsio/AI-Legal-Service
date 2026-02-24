from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    """
    Canonical JSON bytes:
      - UTF-8
      - keys sorted
      - stable separators
      - indent=2
      - newline at EOF
    """
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), indent=2)
    return (s + "\n").encode("utf-8")


def canonical_jsonl_bytes(objs: Iterable[Any]) -> bytes:
    """
    Canonical JSONL bytes:
      - each line is canonical JSON object compressed to one line with sorted keys
      - newline at EOF
    """
    lines: List[str] = []
    for obj in objs:
        line = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        lines.append(line)
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_canonical_json(path: Path, obj: Any) -> None:
    write_bytes(path, canonical_json_bytes(obj))


def write_canonical_jsonl(path: Path, objs: Iterable[Any]) -> None:
    write_bytes(path, canonical_jsonl_bytes(objs))


def read_manifest_json(path: Path) -> Dict[str, str]:
    raw = load_json(path)
    if not isinstance(raw, dict):
        raise ValueError(f"Manifest must be a JSON object: {path}")
    out: Dict[str, str] = {}
    for k, v in raw.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError(f"Manifest entries must be string:string in {path}")
        out[k] = v.lower()
    return out


def write_manifest_json(path: Path, mapping: Dict[str, str]) -> None:
    ordered = {k: mapping[k] for k in sorted(mapping.keys())}
    write_canonical_json(path, ordered)


def assert_no_extra_or_missing_files(expected: Dict[str, str], out_dir: Path) -> None:
    actual_files = sorted(
        str(p.relative_to(out_dir)).replace("\\", "/")
        for p in out_dir.rglob("*")
        if p.is_file()
    )
    expected_files = sorted(expected.keys())

    missing = [f for f in expected_files if f not in actual_files]
    extra = [f for f in actual_files if f not in expected_files]

    if missing:
        raise RuntimeError(f"Missing output files: {', '.join(missing)}")
    if extra:
        raise RuntimeError(f"Unexpected extra output files: {', '.join(extra)}")
