# /casecore-spec/packages/contracts/programs/program_TAGGING.md

# PROGRAM CONTRACT — TAGGING

## Purpose
Apply controlled tag proposals or deterministic tags to artifacts using defined taxonomy rules.

## Type
Deterministic program

## Reads
- facts
- entities
- events
- taxonomy definitions

## Writes
- tag proposal or assignment artifacts
- processing metadata

## Required Rules
- tags must come from governed taxonomy
- no hidden freeform labels as canonical tags
- taxonomy version must be captured
