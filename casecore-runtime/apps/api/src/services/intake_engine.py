"""
INTAKE_ENGINE — Core Service Layer

Orchestrates the intake workflow:
  1. Receives raw narrative -> creates immutable NarrativeRecord
  2. Calls INTERVIEW_AGENT to parse -> creates StructuredIntakeModel
  3. Generates CaseContextRecord from parsed data
  4. Detects gaps -> creates IntakeGapSummary
  5. Manages interview loop (questions <-> responses)
  6. Handles refinement passes
  7. Emits audit events at each transition

State machine:
  CREATED -> INTERVIEWING -> STRUCTURING -> REFINING -> COMPLETE
                                              |
                                              v
                                          ESCALATED
"""

from datetime import datetime, timezone
from typing import Optional

from src.schemas.intake import (
    IntakeStatus,
    IntakeRecord,
    IntakeNarrativeRecord,
    StructuredIntakeModel,
    CaseContextRecord,
    IntakeGapSummary,
    IntakeGap,
    InterviewMessage,
    InterviewSession,
    Party,
    PartyRole,
    Event,
    EventType,
    Relationship,
    TimelineEntry,
    GapType,
    GapSeverity,
)
from src.services.interview_agent import InterviewAgent
from src.services.service_clients import AuditServiceClient
from src.utils.ids import new_id


class IntakeEngine:
    """
    Core intake workflow engine.

    In-memory store for now — swap to persistence client for production.
    """

    def __init__(
        self,
        interview_agent: Optional[InterviewAgent] = None,
        audit_client: Optional[AuditServiceClient] = None,
    ):
        self.agent = interview_agent or InterviewAgent()
        self.audit = audit_client or AuditServiceClient()

        # In-memory stores (replace with persistence layer)
        self._intakes: dict[str, IntakeRecord] = {}
        self._sessions: dict[str, InterviewSession] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_intake(
        self,
        case_id: str,
        narrative: str,
        client_name: Optional[str] = None,
        incident_date: Optional[str] = None,
        case_type_hint: Optional[str] = None,
        jurisdiction_hint: Optional[str] = None,
    ) -> tuple[IntakeRecord, str, list[str]]:
        """
        Start a new intake session.

        Returns: (intake_record, session_id, initial_questions)
        """
        now = datetime.now(timezone.utc)
        intake_id = new_id()
        narrative_id = new_id()
        session_id = new_id()

        # 1. Create immutable narrative record
        narrative_record = IntakeNarrativeRecord(
            narrative_id=narrative_id,
            case_id=case_id,
            original_text=narrative,
            captured_at=now,
            captured_by="client",
            source_method="direct_entry",
        )

        # 2. Create intake record
        intake = IntakeRecord(
            case_id=case_id,
            intake_id=intake_id,
            status=IntakeStatus.INTERVIEWING,
            narrative=narrative_record,
            interview_session_id=session_id,
            created_at=now,
            updated_at=now,
        )

        # 3. Create interview session
        session = InterviewSession(
            session_id=session_id,
            case_id=case_id,
            intake_id=intake_id,
            messages=[
                InterviewMessage(
                    message_id=new_id(),
                    role="client",
                    content=narrative,
                    timestamp=now,
                    metadata={"type": "initial_narrative"},
                )
            ],
            started_at=now,
            updated_at=now,
        )

        # 4. Call INTERVIEW_AGENT to parse narrative
        hints = {}
        if client_name:
            hints["client_name"] = client_name
        if incident_date:
            hints["incident_date"] = incident_date
        if case_type_hint:
            hints["case_type_hint"] = case_type_hint
        if jurisdiction_hint:
            hints["jurisdiction_hint"] = jurisdiction_hint

        try:
            parsed = self.agent.parse_narrative(narrative, hints=hints or None)
            intake.status = IntakeStatus.STRUCTURING

            # 5. Build structured model from parsed output
            structured = self._build_structured_model(case_id, narrative_id, parsed, now)
            intake.structured_model = structured

            # 6. Build case context
            context = self._build_case_context(case_id, parsed, now)
            intake.case_context = context

            # 7. Build gap summary
            gap_summary = self._build_gap_summary(case_id, structured.intake_model_id, parsed, now)
            intake.gap_summary = gap_summary

            # 8. Generate initial follow-up questions
            questions_result = self.agent.generate_questions(
                narrative=narrative,
                structured_model=parsed,
                gaps=[g.model_dump() for g in gap_summary.gaps] if gap_summary.gaps else [],
                conversation_history=[{"role": "client", "content": narrative}],
            )
            initial_questions = questions_result.get("questions", [])

            # Record agent's questions in session
            if initial_questions:
                session.messages.append(
                    InterviewMessage(
                        message_id=new_id(),
                        role="agent",
                        content="\n".join(initial_questions),
                        timestamp=datetime.now(timezone.utc),
                        metadata={"type": "follow_up_questions", "gaps_targeted": questions_result.get("gaps_targeted", [])},
                    )
                )

            intake.status = IntakeStatus.REFINING

        except Exception as e:
            # If AI parsing fails, still create the intake with narrative only
            initial_questions = [
                "Can you identify all parties involved in this matter?",
                "What are the key dates and timeline of events?",
                "What is the primary claim or dispute?",
                "In what jurisdiction did these events occur?",
            ]
            intake.status = IntakeStatus.INTERVIEWING

        intake.updated_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)

        # Store
        self._intakes[intake_id] = intake
        self._sessions[session_id] = session

        # Audit
        self._emit_audit("intake_started", case_id, intake_id)
        self._emit_audit("narrative_captured", case_id, intake_id)
        if intake.structured_model:
            self._emit_audit("narrative_structured", case_id, intake_id)
        if intake.gap_summary and intake.gap_summary.gaps:
            self._emit_audit("gap_detected", case_id, intake_id, {
                "total_gaps": intake.gap_summary.total_gaps,
                "critical_gaps": intake.gap_summary.critical_gaps,
            })

        return intake, session_id, initial_questions

    def respond(
        self,
        intake_id: str,
        session_id: str,
        message: str,
        role: str = "client",
    ) -> tuple[IntakeRecord, list[str], int, int]:
        """
        Process a response from client or attorney.

        Returns: (intake_record, follow_up_questions, new_gaps, resolved_gaps)
        """
        intake = self._intakes.get(intake_id)
        session = self._sessions.get(session_id)
        if not intake or not session:
            raise ValueError(f"Intake {intake_id} or session {session_id} not found")

        now = datetime.now(timezone.utc)

        # Record the response
        session.messages.append(
            InterviewMessage(
                message_id=new_id(),
                role=role,
                content=message,
                timestamp=now,
            )
        )

        old_gap_count = 0
        if intake.gap_summary:
            old_gap_count = len([g for g in intake.gap_summary.gaps if not g.resolved])

        # Refine model with new information
        try:
            current_model = {}
            if intake.structured_model:
                current_model = intake.structured_model.model_dump()
            if intake.gap_summary:
                current_model["gaps"] = [g.model_dump() for g in intake.gap_summary.gaps]

            refined = self.agent.refine_model(
                narrative=intake.narrative.original_text if intake.narrative else "",
                current_model=current_model,
                new_response=message,
                responder_role=role,
            )

            # Update structured model
            narrative_id = intake.narrative.narrative_id if intake.narrative else new_id()
            updated_model = self._build_structured_model(
                intake.case_id, narrative_id, refined, now
            )
            updated_model.version = (intake.structured_model.version + 1) if intake.structured_model else 1
            intake.structured_model = updated_model

            # Update case context
            if "case_context" in refined:
                intake.case_context = self._build_case_context(
                    intake.case_id, refined, now
                )

            # Update gaps
            updated_gaps = self._build_gap_summary(
                intake.case_id,
                updated_model.intake_model_id,
                refined,
                now,
            )
            intake.gap_summary = updated_gaps

            new_gap_count = len([g for g in updated_gaps.gaps if not g.resolved])
            new_gaps_detected = max(0, new_gap_count - old_gap_count)
            gaps_resolved = max(0, old_gap_count - new_gap_count)

            # Generate follow-up questions
            conversation_history = [
                {"role": m.role, "content": m.content}
                for m in session.messages
            ]
            questions_result = self.agent.generate_questions(
                narrative=intake.narrative.original_text if intake.narrative else "",
                structured_model=refined,
                gaps=[g.model_dump() for g in updated_gaps.gaps if not g.resolved],
                conversation_history=conversation_history,
            )
            follow_up = questions_result.get("questions", [])

            # Record agent response
            if follow_up:
                session.messages.append(
                    InterviewMessage(
                        message_id=new_id(),
                        role="agent",
                        content="\n".join(follow_up),
                        timestamp=datetime.now(timezone.utc),
                        metadata={"type": "follow_up_questions"},
                    )
                )

        except Exception:
            follow_up = []
            new_gaps_detected = 0
            gaps_resolved = 0

        intake.refinement_count += 1
        intake.updated_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)

        self._emit_audit("intake_refined", intake.case_id, intake.intake_id, {
            "refinement_count": intake.refinement_count,
            "new_gaps": new_gaps_detected,
            "resolved_gaps": gaps_resolved,
        })

        return intake, follow_up, new_gaps_detected, gaps_resolved

    def get_intake(self, intake_id: str) -> Optional[IntakeRecord]:
        return self._intakes.get(intake_id)

    def get_intake_by_case(self, case_id: str) -> Optional[IntakeRecord]:
        for intake in self._intakes.values():
            if intake.case_id == case_id:
                return intake
        return None

    def get_gaps(self, intake_id: str) -> tuple[Optional[IntakeGapSummary], list[str]]:
        """Returns (gap_summary, suggested_questions)."""
        intake = self._intakes.get(intake_id)
        if not intake or not intake.gap_summary:
            return None, []

        unresolved = [g for g in intake.gap_summary.gaps if not g.resolved]
        questions = [g.suggested_question for g in unresolved if g.suggested_question]
        return intake.gap_summary, questions

    def complete_intake(
        self,
        intake_id: str,
        attorney_notes: Optional[str] = None,
        force_complete: bool = False,
    ) -> tuple[IntakeRecord, int, list[str]]:
        """
        Mark intake as complete.

        Returns: (intake_record, unresolved_gaps, warnings)
        """
        intake = self._intakes.get(intake_id)
        if not intake:
            raise ValueError(f"Intake {intake_id} not found")

        warnings = []
        unresolved = 0

        if intake.gap_summary:
            gaps = intake.gap_summary.gaps
            assessment = self.agent.assess_completeness(
                [g.model_dump() for g in gaps]
            )
            unresolved = len([g for g in gaps if not g.resolved])

            if not assessment["complete"] and not force_complete:
                intake.status = IntakeStatus.ESCALATED
                warnings.append(assessment["reason"])
                warnings.append("Set force_complete=true to override")
                self._emit_audit("intake_escalated", intake.case_id, intake_id, {
                    "reason": assessment["reason"],
                })
                return intake, unresolved, warnings

            if not assessment["complete"] and force_complete:
                warnings.append(f"Force-completed with {unresolved} unresolved gaps")

        now = datetime.now(timezone.utc)
        intake.status = IntakeStatus.COMPLETE
        intake.completed_at = now
        intake.updated_at = now

        # Close interview session
        if intake.interview_session_id:
            session = self._sessions.get(intake.interview_session_id)
            if session:
                session.status = "complete"
                session.updated_at = now

        self._emit_audit("intake_completed", intake.case_id, intake_id, {
            "refinement_count": intake.refinement_count,
            "unresolved_gaps": unresolved,
            "force_completed": force_complete,
        })

        return intake, unresolved, warnings

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_structured_model(
        self, case_id: str, narrative_id: str, parsed: dict, now: datetime
    ) -> StructuredIntakeModel:
        """Convert parsed LLM output into StructuredIntakeModel."""
        parties = []
        for p in parsed.get("parties", []):
            role_str = p.get("role", "unknown")
            try:
                role = PartyRole(role_str)
            except ValueError:
                role = PartyRole.UNKNOWN
            parties.append(Party(
                party_id=new_id(),
                name=p.get("name"),
                role=role,
                description=p.get("description"),
            ))

        events = []
        for e in parsed.get("events", []):
            evt_type_str = e.get("event_type", "other")
            try:
                evt_type = EventType(evt_type_str)
            except ValueError:
                evt_type = EventType.OTHER

            # Map party names to IDs
            party_names = e.get("parties_involved", [])
            party_ids = []
            for name in party_names:
                for p in parties:
                    if p.name and name.lower() in p.name.lower():
                        party_ids.append(p.party_id)
                        break

            events.append(Event(
                event_id=new_id(),
                event_type=evt_type,
                description=e.get("description", ""),
                date_approximate=e.get("date_approximate"),
                date_precision=e.get("date_precision"),
                location=e.get("location"),
                parties_involved=party_ids,
            ))

        relationships = []
        for r in parsed.get("relationships", []):
            relationships.append(Relationship(
                relationship_id=new_id(),
                party_a=r.get("party_a", ""),
                party_b=r.get("party_b", ""),
                relationship_type=r.get("relationship_type", "unknown"),
                description=r.get("description"),
            ))

        timeline = []
        for i, desc in enumerate(parsed.get("timeline_sequence", [])):
            # Try to match to events
            matched_event_id = ""
            for evt in events:
                if desc.lower()[:30] in evt.description.lower():
                    matched_event_id = evt.event_id
                    break
            timeline.append(TimelineEntry(
                event_id=matched_event_id or new_id(),
                sequence_order=i + 1,
                confidence=0.7,
            ))

        return StructuredIntakeModel(
            intake_model_id=new_id(),
            case_id=case_id,
            narrative_id=narrative_id,
            parties=parties,
            events=events,
            relationships=relationships,
            timeline=timeline,
            structured_at=now,
        )

    def _build_case_context(self, case_id: str, parsed: dict, now: datetime) -> CaseContextRecord:
        ctx = parsed.get("case_context", {})
        return CaseContextRecord(
            context_id=new_id(),
            case_id=case_id,
            case_type=ctx.get("case_type"),
            case_subtype=ctx.get("case_subtype"),
            jurisdiction=ctx.get("jurisdiction"),
            claim_categories=ctx.get("claim_categories", []),
            applicable_codes=ctx.get("applicable_codes", []),
            statute_of_limitations=ctx.get("statute_of_limitations_notes"),
            confidence=0.7,
        )

    def _build_gap_summary(
        self, case_id: str, model_id: str, parsed: dict, now: datetime
    ) -> IntakeGapSummary:
        gaps = []
        for g in parsed.get("gaps", []):
            gap_type_str = g.get("gap_type", "missing_info")
            try:
                gap_type = GapType(gap_type_str)
            except ValueError:
                gap_type = GapType.MISSING_INFO

            severity_str = g.get("severity", "medium")
            try:
                severity = GapSeverity(severity_str)
            except ValueError:
                severity = GapSeverity.MEDIUM

            gaps.append(IntakeGap(
                gap_id=new_id(),
                gap_type=gap_type,
                severity=severity,
                description=g.get("description", ""),
                suggested_question=g.get("suggested_question"),
            ))

        critical = len([g for g in gaps if g.severity == GapSeverity.CRITICAL])

        return IntakeGapSummary(
            gap_summary_id=new_id(),
            case_id=case_id,
            intake_model_id=model_id,
            gaps=gaps,
            total_gaps=len(gaps),
            critical_gaps=critical,
            assessed_at=now,
        )

    def _emit_audit(self, event_type: str, case_id: str, intake_id: str, extra: Optional[dict] = None):
        payload = {
            "event_type": event_type,
            "case_id": case_id,
            "intake_id": intake_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            payload.update(extra)
        self.audit.write_event(payload)
