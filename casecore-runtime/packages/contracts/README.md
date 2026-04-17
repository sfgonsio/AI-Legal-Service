# /casecore-runtime/packages/contracts/README.md

# CASECORE RUNTIME CONTRACTS PACKAGE

## Purpose
This package exposes the authoritative CASECORE contracts to runtime code.

## Rules
- runtime must load contracts from this package
- this package is derived from `/casecore-spec/packages/contracts`
- no runtime-only contract invention is allowed
- if authoritative contracts change, this package must be resynced

## Contents
- /authoritative
- /src
- /tests

## Primary Runtime Responsibilities
- resolve authoritative file paths
- load manifest
- locate schemas
- provide contract lookup to validators, pipeline, and APIs
