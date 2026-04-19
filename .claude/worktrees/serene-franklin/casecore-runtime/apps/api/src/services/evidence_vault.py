"""
Evidence Vault — Immutable Evidence Store with Provenance Chain

Every file that enters CaseCore is:
  1. SHA-256 hashed in raw form (before any processing)
  2. Stored permanently in the vault (never deleted)
  3. Assigned a unique evidence_id

Every derived artifact (transcript, key frame, COA match, burden mapping)
gets a DerivationRecord that traces back to the source file through:
  source_hash → derivation_method → parameters → derived_hash

This creates a replicable chain: any claim, COA, burden, or remedy can be
traced back through derived artifacts to the original source file, verified
by its SHA-256 hash. An attorney or judge can follow:

  Legal Theory (COA/Burden/Remedy)
    → Supporting Derivation (transcript @ 2:14-2:38)
      → Source Evidence (SHA-256: abc123...)
        → Original File (video.mp4, verified by hash)

Storage layout on disk:
  {vault_root}/
    manifest.json              — Master index of all evidence + derivations
    sources/
      {sha256_prefix}/
        {sha256}.raw           — Original file (renamed to hash)
        {sha256}.meta.json     — File metadata + chain of custody
    derivations/
      {derivation_id}/
        artifact.*             — The derived file (transcript.txt, frame.png, etc.)
        record.json            — DerivationRecord with full provenance
    theories/
      {theory_id}.json         — COA/Burden/Remedy mapped to derivation chain
"""

import hashlib
import json
import os
import shutil
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Any

from pydantic import BaseModel, Field
from src.utils.ids import new_id

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DerivationMethod(str, Enum):
    """How a derived artifact was produced from source evidence."""
    WHISPER_TRANSCRIPTION = "whisper_transcription"
    FFMPEG_AUDIO_EXTRACT = "ffmpeg_audio_extract"
    FFMPEG_FRAME_CAPTURE = "ffmpeg_frame_capture"
    FFPROBE_METADATA = "ffprobe_metadata"
    OCR_EXTRACTION = "ocr_extraction"
    TEXT_EXTRACTION = "text_extraction"
    PDF_EXTRACTION = "pdf_extraction"
    CLAUDE_COA_MATCH = "claude_coa_match"
    CLAUDE_BURDEN_MAP = "claude_burden_map"
    CLAUDE_TIMELINE_EXTRACT = "claude_timeline_extract"
    MANUAL_ANNOTATION = "manual_annotation"


class TheoryType(str, Enum):
    """Type of legal theory mapped from evidence."""
    CAUSE_OF_ACTION = "cause_of_action"
    BURDEN_ELEMENT = "burden_element"
    REMEDY = "remedy"
    DEFENSE = "defense"
    FACT = "fact"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SourceRecord(BaseModel):
    """Immutable record of a source evidence file in the vault."""
    evidence_id: str
    case_id: str
    sha256: str
    original_filename: str
    file_size_bytes: int
    mime_type: Optional[str] = None
    vault_path: str  # path relative to vault root
    ingested_at: str  # ISO timestamp
    ingested_by: str  # actor: "client", "attorney", "system"
    cloud_source: Optional[str] = None  # e.g. "dropbox:/path/to/file"
    file_metadata: dict = Field(default_factory=dict)  # duration, resolution, etc.


class DerivationRecord(BaseModel):
    """
    Tracks how a derived artifact was produced from source evidence.

    This is the core of the provenance chain. Every derived artifact
    (transcript, frame, COA match) has one of these, linking it back
    to the source file with enough detail to replicate the derivation.
    """
    derivation_id: str
    source_evidence_id: str
    source_sha256: str  # hash of the source file this was derived from
    parent_derivation_id: Optional[str] = None  # for chained derivations

    # What was done
    method: DerivationMethod
    method_version: str  # e.g. "whisper-1", "ffmpeg-8.1", "claude-sonnet-4-20250514"
    parameters: dict = Field(default_factory=dict)
    # e.g. {"sample_rate": 16000, "language": "en", "chunk_index": 0}
    # e.g. {"interval_seconds": 30, "frame_index": 5}
    # e.g. {"coa_code": "CACI-1300", "transcript_range": "2:14-2:38"}

    # What was produced
    artifact_type: str  # "transcript", "audio_wav", "frame_png", "coa_match", "burden_map"
    artifact_path: Optional[str] = None  # path relative to vault root (None for inline)
    artifact_sha256: Optional[str] = None  # hash of the derived artifact
    artifact_inline: Optional[str] = None  # small artifacts stored inline (< 10KB)

    # Timing
    derived_at: str  # ISO timestamp
    processing_seconds: Optional[float] = None

    # For transcript segments specifically
    source_time_start: Optional[float] = None  # seconds into source media
    source_time_end: Optional[float] = None
    confidence: Optional[float] = None


class TheoryMapping(BaseModel):
    """
    Maps a legal theory (COA, burden element, remedy) back through
    the derivation chain to source evidence.

    Theory → Derivation(s) → Source Evidence (SHA-256 verified)
    """
    theory_id: str
    case_id: str
    theory_type: TheoryType
    theory_code: str  # e.g. "CACI-1300", "CACI-1300-element-3"
    theory_description: str

    # The derivation chain supporting this theory
    supporting_derivations: list[str] = Field(default_factory=list)
    # List of derivation_ids that support this claim

    # Direct source evidence links
    source_evidence_ids: list[str] = Field(default_factory=list)

    # Strength assessment
    strength: str = "potential"  # "strong", "moderate", "potential", "weak"
    relevant_excerpt: Optional[str] = None
    notes: Optional[str] = None

    mapped_at: str  # ISO timestamp
    mapped_by: str  # "system", "attorney"


# ---------------------------------------------------------------------------
# Evidence Vault
# ---------------------------------------------------------------------------

class EvidenceVault:
    """
    Immutable evidence store with full provenance chain.

    All source files are SHA-256 hashed and stored permanently.
    All derived artifacts link back to source through DerivationRecords.
    All legal theories link to derivations and source evidence.

    Provides dedup: if a file with the same SHA-256 already exists,
    skip re-processing and return the existing evidence record.
    """

    def __init__(self, vault_root: str):
        self.vault_root = vault_root
        self._sources: dict[str, SourceRecord] = {}      # evidence_id → SourceRecord
        self._by_hash: dict[str, str] = {}                # sha256 → evidence_id
        self._derivations: dict[str, DerivationRecord] = {}  # derivation_id → record
        self._theories: dict[str, TheoryMapping] = {}     # theory_id → mapping

        # Create vault structure
        os.makedirs(os.path.join(vault_root, "sources"), exist_ok=True)
        os.makedirs(os.path.join(vault_root, "derivations"), exist_ok=True)
        os.makedirs(os.path.join(vault_root, "theories"), exist_ok=True)

        # Load existing manifest
        self._load_manifest()

    # ------------------------------------------------------------------
    # Source Evidence
    # ------------------------------------------------------------------

    def hash_file(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file. Does NOT store it."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def has_evidence(self, sha256: str) -> bool:
        """Check if evidence with this hash already exists in vault."""
        return sha256 in self._by_hash

    def get_evidence_by_hash(self, sha256: str) -> Optional[SourceRecord]:
        """Get source record by SHA-256 hash."""
        eid = self._by_hash.get(sha256)
        return self._sources.get(eid) if eid else None

    def ingest_source(
        self,
        file_path: str,
        case_id: str,
        original_filename: str,
        actor: str = "system",
        cloud_source: Optional[str] = None,
        file_metadata: Optional[dict] = None,
        mime_type: Optional[str] = None,
    ) -> tuple[SourceRecord, bool]:
        """
        Ingest a source file into the vault.

        Returns:
            (SourceRecord, is_new) — is_new=False means dedup hit, file already existed.
        """
        # 1. Hash FIRST (before any processing)
        sha256 = self.hash_file(file_path)
        logger.info(f"SHA-256: {sha256[:16]}... for {original_filename}")

        # 2. Dedup check
        if sha256 in self._by_hash:
            existing = self._sources[self._by_hash[sha256]]
            logger.info(f"DEDUP: {original_filename} matches existing evidence {existing.evidence_id}")
            return existing, False

        # 3. Store in vault
        evidence_id = new_id()
        prefix = sha256[:8]
        source_dir = os.path.join(self.vault_root, "sources", prefix)
        os.makedirs(source_dir, exist_ok=True)

        # Copy raw file (preserve original, never modify)
        ext = Path(original_filename).suffix.lower()
        vault_path = os.path.join("sources", prefix, f"{sha256}{ext}")
        full_vault_path = os.path.join(self.vault_root, vault_path)
        shutil.copy2(file_path, full_vault_path)

        # Verify copy integrity
        copy_hash = self.hash_file(full_vault_path)
        if copy_hash != sha256:
            os.remove(full_vault_path)
            raise RuntimeError(f"Vault copy integrity check failed! Source: {sha256}, Copy: {copy_hash}")

        file_size = os.path.getsize(full_vault_path)

        record = SourceRecord(
            evidence_id=evidence_id,
            case_id=case_id,
            sha256=sha256,
            original_filename=original_filename,
            file_size_bytes=file_size,
            mime_type=mime_type,
            vault_path=vault_path,
            ingested_at=datetime.now(timezone.utc).isoformat(),
            ingested_by=actor,
            cloud_source=cloud_source,
            file_metadata=file_metadata or {},
        )

        # Write metadata sidecar
        meta_path = os.path.join(source_dir, f"{sha256}.meta.json")
        with open(meta_path, "w") as f:
            json.dump(record.model_dump(), f, indent=2, default=str)

        # Index
        self._sources[evidence_id] = record
        self._by_hash[sha256] = evidence_id

        self._save_manifest()
        logger.info(f"Ingested source: {evidence_id} ({original_filename}, {file_size} bytes)")
        return record, True

    def get_source_path(self, evidence_id: str) -> Optional[str]:
        """Get the full filesystem path to a source file in the vault."""
        record = self._sources.get(evidence_id)
        if not record:
            return None
        return os.path.join(self.vault_root, record.vault_path)

    def list_sources(self, case_id: Optional[str] = None) -> list[SourceRecord]:
        """List all source records, optionally filtered by case."""
        if case_id:
            return [s for s in self._sources.values() if s.case_id == case_id]
        return list(self._sources.values())

    # ------------------------------------------------------------------
    # Derivations
    # ------------------------------------------------------------------

    def add_derivation(
        self,
        source_evidence_id: str,
        method: DerivationMethod,
        method_version: str,
        artifact_type: str,
        parameters: Optional[dict] = None,
        artifact_file: Optional[str] = None,
        artifact_text: Optional[str] = None,
        parent_derivation_id: Optional[str] = None,
        source_time_start: Optional[float] = None,
        source_time_end: Optional[float] = None,
        confidence: Optional[float] = None,
        processing_seconds: Optional[float] = None,
    ) -> DerivationRecord:
        """
        Record a derivation from source evidence.

        Either artifact_file (path to file to store) or artifact_text
        (inline text for small artifacts) must be provided.
        """
        source = self._sources.get(source_evidence_id)
        if not source:
            raise ValueError(f"Source evidence {source_evidence_id} not found in vault")

        derivation_id = new_id()
        deriv_dir = os.path.join(self.vault_root, "derivations", derivation_id)
        os.makedirs(deriv_dir, exist_ok=True)

        artifact_path = None
        artifact_sha256 = None
        artifact_inline = None

        if artifact_file and os.path.exists(artifact_file):
            # Store artifact file in vault
            ext = Path(artifact_file).suffix.lower()
            dest_name = f"artifact{ext}"
            dest_path = os.path.join(deriv_dir, dest_name)
            shutil.copy2(artifact_file, dest_path)
            artifact_path = os.path.join("derivations", derivation_id, dest_name)
            artifact_sha256 = self.hash_file(dest_path)
        elif artifact_text is not None:
            # Store small text inline
            if len(artifact_text) > 10240:
                # Too big for inline, write to file
                dest_path = os.path.join(deriv_dir, "artifact.txt")
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(artifact_text)
                artifact_path = os.path.join("derivations", derivation_id, "artifact.txt")
                artifact_sha256 = self.hash_file(dest_path)
            else:
                artifact_inline = artifact_text

        record = DerivationRecord(
            derivation_id=derivation_id,
            source_evidence_id=source_evidence_id,
            source_sha256=source.sha256,
            parent_derivation_id=parent_derivation_id,
            method=method,
            method_version=method_version,
            parameters=parameters or {},
            artifact_type=artifact_type,
            artifact_path=artifact_path,
            artifact_sha256=artifact_sha256,
            artifact_inline=artifact_inline,
            derived_at=datetime.now(timezone.utc).isoformat(),
            processing_seconds=processing_seconds,
            source_time_start=source_time_start,
            source_time_end=source_time_end,
            confidence=confidence,
        )

        # Write record to disk
        record_path = os.path.join(deriv_dir, "record.json")
        with open(record_path, "w") as f:
            json.dump(record.model_dump(), f, indent=2, default=str)

        self._derivations[derivation_id] = record
        self._save_manifest()

        logger.info(
            f"Derivation {derivation_id}: {method.value} on {source_evidence_id} "
            f"→ {artifact_type}"
        )
        return record

    def get_derivation(self, derivation_id: str) -> Optional[DerivationRecord]:
        return self._derivations.get(derivation_id)

    def get_derivation_artifact_path(self, derivation_id: str) -> Optional[str]:
        """Get full path to a derivation's artifact file."""
        record = self._derivations.get(derivation_id)
        if not record or not record.artifact_path:
            return None
        return os.path.join(self.vault_root, record.artifact_path)

    def list_derivations(
        self,
        source_evidence_id: Optional[str] = None,
        method: Optional[DerivationMethod] = None,
    ) -> list[DerivationRecord]:
        """List derivations, optionally filtered."""
        results = list(self._derivations.values())
        if source_evidence_id:
            results = [d for d in results if d.source_evidence_id == source_evidence_id]
        if method:
            results = [d for d in results if d.method == method]
        return results

    def get_provenance_chain(self, derivation_id: str) -> list[dict]:
        """
        Walk the full provenance chain from a derivation back to source.

        Returns list of dicts from leaf (most derived) to root (source file):
          [
            {"type": "derivation", "record": DerivationRecord},
            {"type": "derivation", "record": DerivationRecord},  # parent
            {"type": "source", "record": SourceRecord},          # root
          ]
        """
        chain = []
        current = self._derivations.get(derivation_id)

        while current:
            chain.append({"type": "derivation", "record": current})
            if current.parent_derivation_id:
                current = self._derivations.get(current.parent_derivation_id)
            else:
                # Reached the source
                source = self._sources.get(current.source_evidence_id)
                if source:
                    chain.append({"type": "source", "record": source})
                break

        return chain

    # ------------------------------------------------------------------
    # Theory Mapping
    # ------------------------------------------------------------------

    def add_theory(
        self,
        case_id: str,
        theory_type: TheoryType,
        theory_code: str,
        theory_description: str,
        supporting_derivation_ids: list[str],
        strength: str = "potential",
        relevant_excerpt: Optional[str] = None,
        notes: Optional[str] = None,
        mapped_by: str = "system",
    ) -> TheoryMapping:
        """Map a legal theory to its supporting derivation chain."""
        theory_id = new_id()

        # Collect source evidence IDs from derivations
        source_ids = set()
        for did in supporting_derivation_ids:
            d = self._derivations.get(did)
            if d:
                source_ids.add(d.source_evidence_id)

        mapping = TheoryMapping(
            theory_id=theory_id,
            case_id=case_id,
            theory_type=theory_type,
            theory_code=theory_code,
            theory_description=theory_description,
            supporting_derivations=supporting_derivation_ids,
            source_evidence_ids=list(source_ids),
            strength=strength,
            relevant_excerpt=relevant_excerpt,
            notes=notes,
            mapped_at=datetime.now(timezone.utc).isoformat(),
            mapped_by=mapped_by,
        )

        # Write to disk
        theory_path = os.path.join(self.vault_root, "theories", f"{theory_id}.json")
        with open(theory_path, "w") as f:
            json.dump(mapping.model_dump(), f, indent=2, default=str)

        self._theories[theory_id] = mapping
        self._save_manifest()

        logger.info(
            f"Theory {theory_id}: {theory_type.value} {theory_code} "
            f"backed by {len(supporting_derivation_ids)} derivations"
        )
        return mapping

    def list_theories(
        self,
        case_id: Optional[str] = None,
        theory_type: Optional[TheoryType] = None,
    ) -> list[TheoryMapping]:
        results = list(self._theories.values())
        if case_id:
            results = [t for t in results if t.case_id == case_id]
        if theory_type:
            results = [t for t in results if t.theory_type == theory_type]
        return results

    def get_theory_chain(self, theory_id: str) -> dict:
        """
        Get the full chain from theory → derivations → source evidence.

        Returns:
            {
                "theory": TheoryMapping,
                "derivation_chains": [
                    [derivation, ..., source],  # one chain per supporting derivation
                ],
                "source_files": [SourceRecord, ...],  # all unique source files
            }
        """
        theory = self._theories.get(theory_id)
        if not theory:
            return {}

        chains = []
        sources = {}
        for did in theory.supporting_derivations:
            chain = self.get_provenance_chain(did)
            chains.append(chain)
            for link in chain:
                if link["type"] == "source":
                    rec = link["record"]
                    sources[rec.evidence_id] = rec

        return {
            "theory": theory,
            "derivation_chains": chains,
            "source_files": list(sources.values()),
        }

    # ------------------------------------------------------------------
    # Vault Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Summary statistics for the vault."""
        total_size = sum(s.file_size_bytes for s in self._sources.values())
        return {
            "source_files": len(self._sources),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "derivations": len(self._derivations),
            "theories": len(self._theories),
            "unique_hashes": len(self._by_hash),
            "cases": len(set(s.case_id for s in self._sources.values())),
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_manifest(self):
        """Save master manifest to disk."""
        manifest = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "sources": {eid: rec.model_dump() for eid, rec in self._sources.items()},
            "hash_index": dict(self._by_hash),
            "derivations": {did: rec.model_dump() for did, rec in self._derivations.items()},
            "theories": {tid: rec.model_dump() for tid, rec in self._theories.items()},
        }
        manifest_path = os.path.join(self.vault_root, "manifest.json")
        # Write to temp file first, then atomic rename
        tmp_path = manifest_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(manifest, f, indent=2, default=str)
        os.replace(tmp_path, manifest_path)

    def _load_manifest(self):
        """Load manifest from disk if it exists."""
        manifest_path = os.path.join(self.vault_root, "manifest.json")
        if not os.path.exists(manifest_path):
            logger.info(f"No manifest found at {manifest_path}, starting fresh vault")
            return

        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            for eid, data in manifest.get("sources", {}).items():
                self._sources[eid] = SourceRecord(**data)

            self._by_hash = manifest.get("hash_index", {})

            for did, data in manifest.get("derivations", {}).items():
                self._derivations[did] = DerivationRecord(**data)

            for tid, data in manifest.get("theories", {}).items():
                self._theories[tid] = TheoryMapping(**data)

            logger.info(
                f"Loaded vault: {len(self._sources)} sources, "
                f"{len(self._derivations)} derivations, "
                f"{len(self._theories)} theories"
            )
        except Exception as e:
            logger.error(f"Failed to load vault manifest: {e}")


# ---------------------------------------------------------------------------
# Global vault instance
# ---------------------------------------------------------------------------

_vault: Optional[EvidenceVault] = None


def get_evidence_vault(vault_root: Optional[str] = None) -> EvidenceVault:
    """Get or create the global evidence vault."""
    global _vault
    if _vault is None:
        root = vault_root or os.environ.get(
            "CASECORE_VAULT_ROOT",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                         "data", "vault")
        )
        _vault = EvidenceVault(root)
    return _vault
