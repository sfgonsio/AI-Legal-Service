# /casecore-spec/meta/inventories/IMPORT_MAP.md

# IMPORT MAP

## Purpose
Record how imported staging artifacts relate to authoritative files.

## Imported Pack Sources
- `/casecore-spec/_imports/architecture_pack_v1`
- `/casecore-spec/_imports/persistence_ops_pack`
- `/casecore-spec/_imports/control_pack`

## Promoted Files
- `/casecore-spec/_imports/architecture_pack_v1/BUILD_SPEC.md`
  -> `/casecore-spec/docs/architecture/BUILD_SPEC.md`

- `/casecore-spec/_imports/architecture_pack_v1/README.md`
  -> `/casecore-spec/docs/architecture/ARCHITECTURE_PACK_README.md`

- `/casecore-spec/_imports/persistence_ops_pack/DATA_MODEL.md`
  -> `/casecore-spec/database/DATA_MODEL.md`

- `/casecore-spec/_imports/persistence_ops_pack/DATABASE_SCHEMA.sql`
  -> `/casecore-spec/database/ddl/DATABASE_SCHEMA.sql`

- `/casecore-spec/_imports/persistence_ops_pack/SECURITY_ARCHITECTURE.md`
  -> `/casecore-spec/docs/governance/SECURITY_ARCHITECTURE.md`

- `/casecore-spec/_imports/control_pack/docs/governance/GLOSSARY.md`
  -> `/casecore-spec/docs/governance/GLOSSARY.md`

- `/casecore-spec/_imports/control_pack/docs/frontend/DESIGN_SYSTEM_SPEC.md`
  -> `/casecore-spec/docs/frontend/DESIGN_SYSTEM_SPEC.md`

- `/casecore-spec/_imports/control_pack/README.md`
  -> `/casecore-spec/docs/governance/CONTROL_PACK_README.md`

## Rule
`/casecore-spec/_imports` remains staging/import history only and must not be treated as authoritative source.
