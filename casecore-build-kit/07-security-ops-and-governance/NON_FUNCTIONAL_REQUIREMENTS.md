# /casecore-spec/docs/governance/NON_FUNCTIONAL_REQUIREMENTS.md

# NON-FUNCTIONAL REQUIREMENTS

## Purpose
Define the measurable non-functional requirements for CASECORE.

## Performance
- Standard page loads should target under 2 seconds for normal matter dashboards.
- Search responses for indexed content should target under 3 seconds for common queries.
- Workflow status updates should be visible in UI within 5 seconds of completion.

## Scalability
- Architecture must support growth from pilot matters to large multi-document matters without requiring redesign of canonical artifact structures.
- File storage must scale independently from relational persistence.
- Search/index services must scale independently from transaction services.

## Reliability
- Canonical writes must be durable.
- Audit logging must be append-only and durable.
- No silent failure paths are allowed for canonical workflow stages.

## Availability
- MVP target availability: 99.5% or better in production.
- Planned maintenance windows must be logged and controlled.

## Security
- Encryption in transit is mandatory.
- Encryption at rest is mandatory for persisted matter data.
- Matter-level authorization boundaries are mandatory.
- Privileged/restricted content controls are mandatory.

## Observability
- All workflow executions must include run_id.
- Errors must be loggable and queryable by run_id, matter_id, and service name.
- Audit events must be queryable by actor, artifact, and workflow action.

## Accessibility
- Frontend must support keyboard navigation for major review and approval functions.
- Color may not be the sole indicator of status.
- Status must be communicated with label + icon/text, not color alone.

## Retention
- Audit retention may not be shorter than matter data retention unless explicitly governed.
- Deletion rules must follow DATA_LIFECYCLE_POLICY.md.

## Final Rule
CASECORE must optimize for defensibility, traceability, and attorney trust before polish, novelty, or convenience.
