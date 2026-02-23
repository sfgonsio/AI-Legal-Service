# Section 7 — Layered Architecture (Authoritative Wrapper)

**Purpose:** Governance wrapper that binds visuals to the Contract v1 source of truth.

**Contract Version:** v1 (locked)

**SSOT source (authoritative):** `contract/v1/architecture/section7-layered-architecture.md`

If any conflict exists between this page, diagrams, or other docs:
**the Contract v1 SSOT source governs.**

---

## Drift Control (Non-Negotiable)

These visuals MUST NOT introduce or imply:
- new layers or services
- new data paths or persistence zones
- new authority flows or trust boundaries
- new tool access patterns
- new logging/audit semantics

If drift is detected:
1) update Contract v1 SSOT first  
2) regenerate visuals to match SSOT  
3) re-render any derived docs last

---

## Visual References

### Section 7 (Authoritative)
<img src="../../legacy/assets/svg/section7-authoritative.svg" alt="Section 7 Authoritative" />

### Layer 3 (Figma)
<img src="../../legacy/assets/svg/layer3-figma.svg" alt="Layer 3 Figma" />

### Bridge Mapping
<img src="../../legacy/assets/svg/bridge-mapping.svg" alt="Bridge Mapping" />

---

## Next
- Finalize `contract/v1/architecture/section7-layered-architecture.md` (authoritative text)
- Add schemas and tool interface contracts under `contract/v1/schemas/`
- Add governance/taxonomy artifacts under `contract/v1/taxonomies/`


