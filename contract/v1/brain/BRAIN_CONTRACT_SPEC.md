# BRAIN_CONTRACT_SPEC.md

```markdown
# Brain Contract Specification

## Version
v1.0

---

## 1. Purpose

The Brain is a governed, staged reasoning system that transforms normalized evidence into legal structure and strategic outputs. It is designed to be smart, contextual, and legally grounded while maintaining explicit contracts at each transformation stage.

The Brain processes evidence through controlled stages with measurable inputs, outputs, and confidence markers. It does not reason on raw messages directly. It does not mutate evidence truth. It preserves uncertainty and provenance throughout.

---

## 2. Brain Design Principles

### 2.1 No Direct Reasoning on Raw Messages
The Brain never reasons on unprocessed message text. All inputs must be normalized first.
- Raw messages → Normalization → Structured Objects → Brain Processing

### 2.2 Evidence Truth is Immutable
The Brain reads evidence; it does not mutate or reinterpret original source material.
- Normalization creates canonical representations
- Brain adds structure, classification, and legal mapping
- Original evidence record remains unchanged

### 2.3 Explicit Uncertainty is Required
The Brain must emit confidence scores and ambiguity markers at every stage.
- No false certainty
- Conflicting evidence is labeled as such
- Missing data is marked as "insufficient_data"
- Unresolved identities are flagged

### 2.4 Every Legal Conclusion Traces to Source + Authority
A legal conclusion (COA, burden element, remedy) is invalid without:
- Source fact/event ID
- Source authority record (regulation, rule, instruction)
- Confidence score
- Unresolved gaps (if any)

### 2.5 Attorney Governs Promotions
The Brain proposes; the attorney disposes.
- Brain may classify, map, and suggest
- Attorney approval required for final legal conclusions
- Review boundaries are explicit

### 2.6 Context Must Be Modeled, Not Implied
Contextual relationships are explicit in the graph, not assumed.
- Actor relationships are edges with confidence
- Event sequences are timestamped and sourced
- Third-party references are tracked
- Repeated mentions across sources are linked

### 2.7 Staged Outputs Are Required
Each stage produces a complete, usable contract before the next stage begins.
- Normalization → Classified Statements
- Classification → Actor Graph
- Relationships → Timeline
- Timeline → Legal Mappings
- Mappings → Strategic Inputs

No stage feeds directly from raw input of a prior stage.

---

## 3. Brain Stage Model

### 3.1 Stage 1: Normalization

**Input Contract:**
```
normalized_message_set: [
  {
    message_id,
    case_id,
    source_actor_id,
    timestamp,
    channel,
    text_body,
    raw_message_id,
    trust_level
  }
]

normalized_interview_set: [
  {
    interview_id,
    case_id,
    interview_date,
    interviewer_id,
    subject_actor_id,
    transcript_segments: [
      {
        segment_id,
        speaker,
        timestamp,
        text,
        confidence
      }
    ]
  }
]

normalized_document_set: [
  {
    document_id,
    case_id,
    document_type,
    date_created,
    extracted_text,
    key_extracts: [
      {
        extract_id,
        text,
        context,
        relevance_score
      }
    ]
  }
]
```

**Output Contract:**
```
structured_normalized_objects: [
  {
    object_id,
    source_type,     // message | interview | document
    source_id,
    case_id,
    normalized_text,
    segments: [
      {
        segment_id,
        statement_text,
        source_speaker_or_author,
        original_timestamp,
        normalized_timestamp
      }
    ],
    metadata: {
      extracted_entities: [],
      extracted_dates: [],
      extracted_locations: [],
      quality_score
    }
  }
]
```

**Quality Gate:** All extracts must be trace-linked to source document. No information loss.

---

### 3.2 Stage 2: Statement Classification

**Input Contract:**
```
statement_input_set: [
  {
    segment_id,
    statement_text,
    source_actor_id,
    source_timestamp,
    context_window,
    document_type
  }
]
```

**Output Contract:**
```
classified_statement_set: [
  {
    statement_id,
    source_segment_id,
    case_id,
    statement_text,
    classification: {
      primary_type: "fact" | "allegation" | "opinion" | "legal_conclusion" | "hearsay" | "speculation" | "emotional_language" | "request_instruction",
      secondary_types: [],
      confidence: 0.0-1.0
    },
    legal_relevance: {
      potentially_relevant: boolean,
      justification: string,
      relevance_score: 0.0-1.0
    },
    source_metadata: {
      actor_id,
      timestamp,
      context,
      source_document_id
    },
    uncertainty_markers: {
      ambiguous: boolean,
      reason: string,
      requires_manual_review: boolean
    }
  }
]
```

**Classification Rules:**
- **Fact**: Observable event, directly witnessed, testable
- **Allegation**: Claim made by one actor about another; may be disputed
- **Opinion**: Subjective interpretation; lacks direct observation
- **Legal Conclusion**: Statement of law, liability, or remedy
- **Hearsay**: A says B told A that X (second-hand report)
- **Speculation**: "Might have," "could be," "probably"
- **Emotional Language**: Adjectives without factual content
- **Request/Instruction**: Action request, command, or procedural instruction

---

### 3.3 Stage 3: Actor & Relationship Graph

**Input Contract:**
```
actor_input_set: [
  {
    actor_id,
    display_name,
    actor_type,
    source_mentions: [
      {
        statement_id,
        context,
        mentioned_as,
        confidence
      }
    ]
  }
]

relationship_candidates: [
  {
    actor_a_id,
    actor_b_id,
    relationship_type,
    source_statements: [],
    confidence
  }
]
```

**Output Contract:**
```
actor_graph: {
  actors: [
    {
      actor_id,
      display_name,
      actor_type,
      role_candidates: [
        {
          role: "plaintiff" | "defendant" | "witness" | "expert" | "custodian",
          confidence,
          source_statements: []
        }
      ],
      organization_affiliation: string,
      first_mention_statement_id,
      last_mention_statement_id,
      mention_count,
      identity_confidence: 0.0-1.0,
      identity_unresolved_markers: []
    }
  ],
  relationships: [
    {
      actor_a_id,
      actor_b_id,
      relationship_type: "employed_by" | "reports_to" | "knows" | "related_to" | "referenced_by",
      confidence: 0.0-1.0,
      source_statements: [],
      bidirectional: boolean,
      unresolved: boolean,
      unresolved_reason: string
    }
  ],
  third_party_references: [
    {
      reference_id,
      referenced_name,
      referenced_in_statements: [],
      potential_actor_matches: [],
      resolution_status: "resolved" | "ambiguous" | "unresolved"
    }
  ]
}
```

**Graph Construction Rules:**
- Actors are nodes
- Relationships are directed edges with confidence
- Third-party references (A mentions C) are tracked separately
- Identity collisions (multiple similar names) are flagged
- Confidence scores reflect mention consistency

---

### 3.4 Stage 4: Timeline & Event Assembly

**Input Contract:**
```
event_candidates: [
  {
    statement_id,
    event_text,
    stated_timestamp,
    inferred_timestamp,
    mentioned_actors: [],
    event_type,
    source_reliability
  }
]
```

**Output Contract:**
```
event_timeline: {
  events: [
    {
      event_id,
      event_description,
      canonical_timestamp,
      timestamp_confidence: 0.0-1.0,
      event_type: "action" | "communication" | "state_change" | "discovery" | "incident",
      source_statements: [
        {
          statement_id,
          actor_id,
          timestamp_stated,
          text
        }
      ],
      involved_actors: [],
      event_sequence: [],
      contradictions: [
        {
          event_id,
          contradiction_type: "timeline" | "facts" | "actors",
          source_statements: [],
          resolution: "unresolved" | "resolved_as"
        }
      ],
      gaps: [
        {
          gap_id,
          gap_description,
          required_evidence,
          criticality
        }
      ]
    }
  ],
  event_chains: [
    {
      chain_id,
      event_sequence: [],
      causal_links: [
        {
          from_event_id,
          to_event_id,
          causal_confidence: 0.0-1.0,
          justification
        }
      ],
      narrative_summary
    }
  ],
  timeline_confidence: 0.0-1.0,
  unresolved_timeline_markers: []
}
```

**Timeline Rules:**
- Events are ordered by canonical timestamp
- Contradictions are explicit (two events cannot occupy same time)
- Causal links are marked with confidence
- Missing events are inferred when gaps are apparent
- Source statements are always traceable

---

### 3.5 Stage 5: Legal Mapping

**Input Contract:**
```
authority_pack_inputs: [
  {
    authority_id,
    case_id,
    authority_type: "statute" | "regulation" | "contract" | "instruction",
    authority_text,
    applicable_coas: [],
    applicable_burdens: [],
    applicable_elements: [],
    applicable_remedies: []
  }
]

fact_event_input_set: [
  {
    fact_id,
    fact_text,
    event_id,
    source_statement_ids: [],
    involved_actors: [],
    timestamp
  }
]
```

**Output Contract:**
```
legal_mapping_set: [
  {
    mapping_id,
    case_id,
    mapping_type: "coa_candidate" | "burden_support" | "element_support" | "remedy_support" | "fact_to_element",
    fact_ids: [],
    event_ids: [],
    actor_ids: [],
    authority_id,
    authority_section: string,
    authority_text: string,
    legal_conclusion_text: string,
    confidence: 0.0-1.0,
    unresolved_gaps: [
      {
        gap_id,
        gap_type,
        required_evidence,
        blocking: boolean
      }
    ],
    contradictions: [
      {
        conflicting_mapping_id,
        conflict_type,
        resolution_status
      }
    ],
    requires_attorney_review: boolean,
    review_reason: string,
    traceability: {
      source_facts: [],
      source_events: [],
      source_actors: [],
      authority_linkage: true
    }
  }
]
```

**Legal Mapping Rules:**
- NO legal conclusion without authority linkage
- Facts and events must be sourced
- Actors involved must be explicit
- Confidence reflects fact quality + authority clarity
- Unresolved gaps must be stated
- Contradictions are tracked

---

### 3.6 Stage 6: Strategic Derivation

**Input Contract:**
```
legal_mapping_set: [legal_mapping_set from Stage 5]

actor_graph: [actor_graph from Stage 3]

event_timeline: [event_timeline from Stage 4]
```

**Output Contract:**
```
warroom_strategy_input_set: {
  coverage_input: {
    burden_id: {
      element_id: {
        supporting_facts: [],
        supporting_events: [],
        corroborating_actors: [],
        coverage_score: 0.0-1.0,
        confidence: 0.0-1.0,
        gaps: []
      }
    }
  },
  assumption_candidates: [
    {
      assumption_id,
      assumption_text,
      criticality: "critical" | "high" | "medium",
      failure_impact: -X%,
      validation_method,
      required_evidence: []
    }
  ],
  discovery_targets: [
    {
      target_id,
      target_description,
      target_type: "fact_gap" | "timeline_gap" | "contradiction_resolution" | "expert_opinion",
      supporting_burden_id,
      priority: "critical" | "high" | "medium",
      estimated_difficulty
    }
  ],
  scenario_inputs: {
    available_coas: [],
    available_burdens: [],
    available_remedies: [],
    key_actors: [],
    primary_evidence: [],
    critical_contradictions: []
  },
  strategic_confidence: {
    coverage_confidence: 0.0-1.0,
    timeline_confidence: 0.0-1.0,
    actor_confidence: 0.0-1.0,
    legal_mapping_confidence: 0.0-1.0,
    overall_strategic_readiness: "sufficient" | "needs_development" | "insufficient_data"
  }
}
```

---

## 4. Input Contracts

### 4.1 normalized_message_set
Messages extracted from email, chat, SMS, documents with metadata.

### 4.2 normalized_interview_set
Interview transcripts segmented with speaker identification and timestamps.

### 4.3 normalized_document_set
Documents with extracted text, key phrases, and metadata.

### 4.4 actor_registry
All actors in the case with basic metadata.

### 4.5 timeline_candidates
Date/time references extracted from all sources.

### 4.6 authority_pack_inputs
Legal authorities (statutes, contracts, instructions) applicable to the case.

### 4.7 evidence_inventory_view
Linked evidence records with trust levels and source provenance.

---

## 5. Output Contracts

| Stage | Output Contract |
|-------|-----------------|
| 1 | structured_normalized_objects |
| 2 | classified_statement_set |
| 3 | actor_graph |
| 4 | event_timeline |
| 5 | legal_mapping_set |
| 6 | warroom_strategy_input_set |

---

## 6. Confidence Model by Stage

### 6.1 Normalization Confidence
Measures extraction quality and completeness.
- 0.95-1.0: Clean, complete extraction
- 0.75-0.94: Minor OCR/encoding issues, recoverable
- 0.50-0.74: Partial extraction, missing sections
- <0.50: Insufficient data extracted; requires manual review

### 6.2 Statement Classification Confidence
Measures clarity of statement type.
- 0.95-1.0: Unambiguous fact or opinion
- 0.75-0.94: Clear classification, minor uncertainty
- 0.50-0.74: Multiple plausible classifications
- <0.50: Ambiguous; requires manual review

### 6.3 Actor Resolution Confidence
Measures certainty of actor identity.
- 0.95-1.0: Same person/entity mentioned consistently
- 0.75-0.94: High consistency, minor naming variation
- 0.50-0.74: Probable match, some ambiguity
- <0.50: Unresolved identity collision; flagged for review

### 6.4 Timeline Confidence
Measures event sequence certainty.
- 0.95-1.0: Precise timestamps, no contradictions
- 0.75-0.94: Clear sequence, minor date uncertainty
- 0.50-0.74: Probable sequence, gaps present
- <0.50: Contradictory timeline; unresolved

### 6.5 Legal Mapping Confidence
Measures fact-to-law linkage clarity.
- 0.95-1.0: Direct statutory language match
- 0.75-0.94: Clear authority link, minor interpretation
- 0.50-0.74: Arguable interpretation, gaps present
- <0.50: Weak authority link; requires attorney review

### 6.6 Strategic Confidence
Overall readiness for War Room input.
- sufficient: All burdens have ≥0.7 coverage, <3 unresolved gaps
- needs_development: Some burdens <0.7 coverage, discoverable gaps
- insufficient_data: Multiple critical gaps, missing evidence

---

## 7. Legal Authority Application Rules

### 7.1 Authority Linkage is Mandatory
Every legal conclusion must reference:
- authority_id
- authority_section
- authority_text_excerpt
- applicable_fact_ids
- applicable_event_ids

### 7.2 Authority Scope
An authority applies only to stated legal domains:
- If authority governs "negligence," it does not govern "contract breach"
- If authority is a contract, it applies only to parties to that contract
- If authority is case law, precedent scope is explicit

### 7.3 Authority Conflict Resolution
When two authorities conflict:
- Preserve both mappings
- Mark as "conflicting"
- Emit confidence reduction
- Flag for attorney resolution

### 7.4 Authority Updates
If authority is updated during case:
- Prior mappings are marked as "authority_version_X"
- New mappings use current authority
- Both are preserved for audit

---

## 8. Contextual Awareness Rules

### 8.1 Cross-Message Story Assembly
If Actor A mentions Actor B in Message 1, and Actor B mentions Actor A in Message 2:
- Relationship edge is created in actor_graph
- Bidirectionality is tested (A→B only vs. mutual)
- Confidence is reduced if story conflicts

### 8.2 Third-Person References
If A says "John told me X":
- John is identified as third-party reference
- John's actual statement (if any) is linked separately
- Hearsay classification is applied

### 8.3 Relationship Inference
If A reports-to B, and B reports-to C:
- Transitive relationship is inferred (A reports through B to C)
- Confidence is reduced at each inference step
- Confirmation source is tracked

### 8.4 Repeated Mentions
If Actor A is mentioned 5 times across 3 messages:
- Mention count is tracked
- Consistency is measured
- Conflicting descriptions are flagged

### 8.5 Conflicting Accounts
If A says "X happened on Monday" and B says "X happened on Wednesday":
- Both statements are preserved
- Event_timeline marks contradiction
- Resolution status is "unresolved" until clarified

### 8.6 One Fact, Multiple Elements
If Fact F supports both Burden_1.Element_A and Burden_2.Element_B:
- Fact F is linked to both elements
- Both mappings preserve the link
- Coverage calculation uses the same source for both

### 8.7 Actor Appears Differently
If Actor A is described as "CEO" in one message and "Manager" in another:
- Both descriptions are preserved
- Identity confidence is reduced
- Requires manual review if role is legally material

---

## 9. Promotion / Review Boundaries

### 9.1 Brain May Propose (No Review Required)
- Actor identity classifications
- Event timelines
- Relationship edges
- Statement classifications
- Fact-to-statute mappings (with authority linkage)

### 9.2 Attorney Review Required Before Promotion
- Final actor role assignment (plaintiff, defendant, witness)
- COA selection (which legal theory to pursue)
- Burden coverage sufficiency (when coverage ≥ 0.7)
- Remedy selection (which remedies to claim)
- High-stakes assumptions (criticality = "critical")
- Contradiction resolutions (when multiple interpretations exist)

### 9.3 Automation Allowed (No Attorney Review)
- Confidence scoring
- Gap identification
- Source tracing
- Uncertainty markers
- Data sufficiency assessment

---

## 10. Audit / Traceability Requirements

Every Brain output must be traceable:

```
{
  output_id,
  source_artifacts: [
    {
      artifact_type: "message" | "interview" | "document",
      artifact_id,
      extract_id
    }
  ],
  source_statements: [
    {
      statement_id,
      classification,
      actor_id,
      timestamp
    }
  ],
  source_facts: [
    {
      fact_id,
      event_id,
      supporting_statements: []
    }
  ],
  source_actors: [
    {
      actor_id,
      display_name,
      role_in_output
    }
  ],
  source_authority: [
    {
      authority_id,
      authority_section,
      linkage_confidence
    }
  ],
  transformation_chain: [
    {
      stage: 1-6,
      transformation_logic,
      timestamp
    }
  ]
}
```

---

## 11. Failure States / Insufficient Data Rules

### 11.1 Ambiguous
Used when multiple equally plausible interpretations exist.
- Example: "Jim might have known" — fact or speculation?
- Resolution: Manual review required

### 11.2 Conflicting
Used when two credible sources contradict.
- Example: "X happened Monday" vs. "X happened Wednesday"
- Resolution: Requires fact-finding

### 11.3 Insufficient_Data
Used when required evidence is missing.
- Example: Timeline has no events for March 2024
- Resolution: Discovery needed

### 11.4 Unresolved_Identity
Used when actor cannot be reliably matched.
- Example: "John Smith" appears twice; same person?
- Resolution: Manual clarification

### 11.5 Unresolved_Timeline
Used when events cannot be sequenced.
- Example: Contradictory dates across sources
- Resolution: Requires event clarification

### 11.6 Unresolved_Authority_Mapping
Used when fact does not clearly map to legal authority.
- Example: Fact F potentially supports Burden_A OR Burden_B, not clear which
- Resolution: Legal interpretation required

### 11.7 Insufficient Coverage
Used when coverage score < 0.6 for a burden.
- Meaning: Element lacks sufficient supporting evidence
- Resolution: Discovery planning

---

## 12. Testability Requirements

The Brain must pass a golden test corpus with:

### 12.1 Complex Message Chains
- A texts B about C
- B forwards A's text to D with commentary
- D replies to B (not A)
- Result: Hearsay chain is properly classified

### 12.2 Quoted Email Chains
- Email 1 from A to B
- Email 2 is B's reply to A, quoting Email 1
- Email 3 is A's reply, quoting both prior emails
- Result: Statement ownership and quotes are correctly tracked

### 12.3 Forwarded Content
- Original message from A
- Forwarded by B to C with "FYI, see below"
- Forwarded by C to D
- Result: Original author (A) is preserved; forward chain is tracked

### 12.4 Contradictory Witnesses
- Witness 1 says "X happened at 3pm"
- Witness 2 says "X happened at 5pm"
- Witness 3 confirms Witness 1
- Result: Contradiction is explicit; corroboration is tracked

### 12.5 Partial Evidence Across Sources
- Document 1 mentions "John Smith discussed project"
- Interview with "JS" confirms same project
- Email from "Smith, J" refers to "the project we discussed"
- Result: Identity is resolved (confidence 0.85+)

### 12.6 Similar Names
- Actor "John Smith" mentioned in 2 messages
- Actor "John Smithson" mentioned in 1 message
- Actor "J. Smith" mentioned in 3 messages
- Result: Collision is flagged; manual review recommended

### 12.7 One Fact Supporting Multiple Burdens
- Fact: "Acme failed to inspect the equipment"
- Maps to Burden_1 (negligence) Element_A (breach of duty)
- Maps to Burden_2 (product liability) Element_B (defective design)
- Result: Both mappings preserve source fact; no duplication

---

## 13. Open Questions / Deferred Decisions

### 13.1 Confidence Score Distribution
How are confidence scores calibrated? What is the ground truth?
- Current: Based on source consistency and authority clarity
- Deferred: Validation against attorney review patterns

### 13.2 Contextual Inference Depth
How many degrees of transitive inference are allowed?
- Current: 1-2 degrees (A→B→C)
- Deferred: Empirical testing on case data

### 13.3 Authority Temporal Scope
If an authority changes mid-case, which version applies to prior events?
- Current: All events use applicable authority at event time
- Deferred: Case-specific rules may override

### 13.4 Assumption Criticality Calibration
How is "criticality" determined for assumptions?
- Current: Based on coverage impact (if assumption fails, coverage drops >X%)
- Deferred: Attorney input on litigation risk

### 13.5 Hearsay Depth Tracking
How many levels of "A said B said C said" can the Brain track?
- Current: 2-3 levels with confidence reduction
- Deferred: Performance testing on real cases

### 13.6 Actor Identity Confidence Threshold
What minimum confidence (0.5? 0.7? 0.9?) requires manual resolution?
- Current: <0.7 is flagged for review
- Deferred: Attorney preference by case

### 13.7 Strategic Readiness Thresholds
What coverage score (0.6? 0.7? 0.8?) indicates "sufficient" coverage?
- Current: ≥0.7 for primary burdens
- Deferred: Varies by claim type and jurisdiction

---

## Appendix A: Contract Notation

Contracts are defined in JSON schema format with:
- Required fields (no default)
- Optional fields (nullable)
- Enumerated values (pipe-separated)
- Confidence scores (0.0-1.0, float)
- Timestamps (ISO 8601)
- IDs (case-scoped, string)

All outputs are traceable to inputs. All transformations are logged.

---

## Appendix B: Governance

- **Input Control**: Evidence stratum owns input contracts
- **Processing**: Brain applies staged transformation
- **Output Gating**: Attorney governs promotion from proposals to conclusions
- **Audit**: All transformations are logged and traceable
- **Update**: This specification may be updated with case-specific rules

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-21 | Initial specification |

```