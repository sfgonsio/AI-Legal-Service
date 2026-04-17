# /casecore-spec/packages/contracts/programs/program_COMPOSITE_ENGINE.md

# PROGRAM CONTRACT — COMPOSITE_ENGINE

## Purpose
Organize facts into event candidates and composite event structures.

## Type
Deterministic program

## Reads
- fact artifacts
- entity references
- timestamps/date cues
- prior event proposals where governed

## Writes
- event proposal artifacts
- composite-event support structures
- timeline support records

## Required Rules
- conflicting support must not be silently collapsed
- fact lineage must be preserved
- event proposals remain distinct from canonical events until governed promotion
