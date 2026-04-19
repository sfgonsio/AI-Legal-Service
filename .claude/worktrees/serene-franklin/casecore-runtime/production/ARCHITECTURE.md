# CaseCore Architecture

## System Overview

CaseCore is a legal case management and strategy platform designed to help attorneys build cases methodically through evidence-based weapons, strategic planning, and real-time deposition assistance.

### High-Level Flow

```
1. Client uploads evidence (PDFs, emails, documents)
   ↓
2. System extracts text, calculates hash, decomposes into facts
   ↓
3. Facts mapped to Causes of Action (COAs) against CACI Jury Instructions
   ↓
4. Burden elements identified and evidence scored
   ↓
5. Attorney reviews, approves/flags Causes of Action
   ↓
6. Weapon arsenal built (26 interrogatories with what-if simulation)
   ↓
7. Strategies orchestrated across weapons
   ↓
8. Real-time deposition assistant suggests questions based on live testimony
```

## Tech Stack Rationale

The real-time deposition feature drives all architecture decisions:

**Why FastAPI + WebSocket?**
- Native async/await for high-throughput, low-latency operations
- First-class WebSocket support for real-time bidirectional communication
- Type-safe with Pydantic validation
- Fast startup and deployment
- Perfect for handling 10-100 concurrent depositions

**Why SQLite (migrate to PostgreSQL)?**
- SQLite sufficient for initial deployment (single case at a time)
- Zero external dependencies reduces deployment complexity
- AsyncIO SQLite (aiosqlite) maintains async consistency
- Clear migration path to PostgreSQL for multi-tenant production

**Why React?**
- Real-time UI updates for deposition feed
- Responsive component-based architecture
- Lightweight bundle for mobile attorney devices
- Integrates seamlessly with WebSocket via custom hooks

## Database Schema

### Core Tables

```
CASES
├── id (PK)
├── name (e.g., "Mills v. Polley")
├── court
├── plaintiff / defendant
├── status (active, resolved, archived)
├── created_at

DOCUMENTS
├── id (PK)
├── case_id (FK)
├── filename
├── file_type (pdf, email, image, etc.)
├── text_content (extracted text)
├── char_count
├── sha256_hash (integrity verification)
├── created_at

COAS (Causes of Action)
├── id (PK)
├── case_id (FK)
├── name (e.g., "Breach of Contract")
├── caci_ref (CACI jury instruction reference)
├── strength (0-100 confidence score)
├── evidence_count
├── coverage_pct (% of case covered)
├── status (pending, approved, flagged)

BURDEN_ELEMENTS
├── id (PK)
├── coa_id (FK)
├── element_id (e.g., "B1", "B2", "B3")
├── description
├── strength (evidence supporting this element)
├── supporting_docs (JSON array of doc IDs)

WEAPONS
├── id (PK)
├── case_id (FK)
├── category (DISCOVER, UNCOVER, WEAPONIZE)
├── coa_ref (which COA this strengthens)
├── caci (CACI reference)
├── strategy (e.g., "Document Pincer")
├── question (the actual deposition question)
├── strengthens_jeremy (what Jeremy gains)
├── weakens_david (what defendant loses)
├── perjury_push (how this creates perjury opportunity)
├── evidence_score (0-100)
├── perjury_trap (boolean)
├── docs_json (associated documents)
├── attorney_notes (attorney edits)
├── status (pending, deployed, used)

STRATEGIES
├── id (PK)
├── case_id (FK)
├── name (e.g., "Document Pincer")
├── emoji
├── weapons_json (IDs of weapons in this strategy)
├── rationale
├── value_score / depo_impact / trial_impact
├── phases_json (discovery, deposition, trial)

PERJURY_PATHS
├── id (PK)
├── case_id (FK)
├── name (e.g., "Financial Trap")
├── desc
├── weapons_json (weapons that spring this trap)
├── logic (what makes this a trap)
├── trap_springs (when the trap activates)

DEPOSITION_SESSIONS
├── id (PK)
├── case_id (FK)
├── witness_name
├── started_at / ended_at
├── status (active, closed, archived)
├── transcript_text

ATTORNEY_EDITS (Audit Trail)
├── id (PK)
├── weapon_id (FK)
├── field_name (what was edited)
├── original_value / edited_value
├── status (staged, approved, deployed)
├── timestamp
```

### Relationships

```
Case
├── 1→N Documents
├── 1→N COAs
│   └── 1→N BurdenElements
├── 1→N Weapons
├── 1→N Strategies
├── 1→N PerjuryPaths
└── 1→N DepositionSessions

Weapon
└── 1→N AttorneyEdits
```

## API Endpoint Catalog

### Cases
```
POST   /cases                    Create case
GET    /cases                    List cases
GET    /cases/{id}               Get case detail with all related data
PATCH  /cases/{id}               Update case
DELETE /cases/{id}               Delete case
```

### Weapons
```
GET    /weapons?case_id={id}     List weapons for case
GET    /weapons/{id}             Get weapon detail
PATCH  /weapons/{id}             Update weapon (attorney edits tracked)
POST   /weapons/{id}/simulate    Simulate opposition response (opposition_agent)
POST   /weapons/{id}/deploy      Mark weapon as deployed
```

### Strategies
```
GET    /strategies?case_id={id}  List strategies
GET    /strategies/{id}          Get strategy with weapons
GET    /strategies/case/{id}     Get all strategies for case
```

### COAs
```
GET    /coas?case_id={id}        List COAs
GET    /coas/{id}                Get COA with burden elements
GET    /coas/case/{id}           Get all COAs for case
```

### Documents
```
GET    /documents?case_id={id}   List documents
GET    /documents/{id}           Get document with full text
GET    /documents/case/{id}      Get all documents for case
```

### Deposition
```
POST   /deposition/sessions                 Create deposition session
GET    /deposition/sessions/{id}            Get session
GET    /deposition/sessions/case/{id}       Get case sessions
PATCH  /deposition/sessions/{id}/transcript Update transcript
PATCH  /deposition/sessions/{id}/close      Close session
WS     /deposition/ws/{session_id}          WebSocket for real-time feed

WebSocket Messages:
  IN:  {"type": "testimony", "text": "...", "witness_name": "..."}
  OUT: {"type": "suggestion", "follow_up_questions": [...], "contradictions": [...], "perjury_flag": {...}}
```

## AI Agent Architecture

### Four Agents with Async/Await Interface

**1. opposition_agent.py**
- **Input:** Weapon object with strategy, evidence, question
- **Output:** Predicted defense response {david_says, counter, delta, perjury_evidence}
- **Method:** Canned responses keyed by strategy name + scoring based on evidence_score
- **Integration:** Called by `/weapons/{id}/simulate` endpoint
- **Future:** Claude API for dynamic defense simulation

**2. strategy_agent.py**
- **Input:** Available weapons, case_state (proven COAs, deposed witnesses, etc.)
- **Output:** Weapon recommendation + sequence strategy
- **Method:** Scoring function: base_score + (unproven_coa_bonus) + (perjury_trap_boost) - (deployed_duplicates_penalty)
- **Integration:** Called by dashboard to recommend next weapon
- **Future:** Multi-turn Claude planning for optimal weapon sequencing

**3. deposition_agent.py**
- **Input:** Testimony chunk, evidence library, available weapons
- **Output:** Follow-up questions, contradiction flags, perjury opportunities
- **Method:** Keyword matching against evidence + testimony analysis
- **Integration:** Called in real-time via WebSocket during deposition
- **Future:** Claude API for live testimony analysis + natural language follow-ups

**4. document_agent.py**
- **Input:** Document filename, extracted text, COA list
- **Output:** COA relevance scores, key passages, burden element matches
- **Method:** Text extraction + keyword matching to COAs + burden elements
- **Integration:** Called on document upload
- **Future:** Claude API for semantic similarity matching

### Future Claude API Integration

Each agent will have a Future integration path:

```python
# opposition_agent.py - Future
async def predict_defense_response_claude(weapon, client):
    response = await client.messages.create(
        model="claude-opus-4",
        max_tokens=500,
        system="You are opposing counsel defending against this weapon. Respond realistically.",
        messages=[
            {"role": "user", "content": f"Weapon: {weapon.strategy}\nQuestion: {weapon.question}\nRespond as defendant"}
        ]
    )
    return parse_defense_response(response.content)
```

## Real-Time Deposition Architecture

### Deposition Flow

```
Attorney opens deposition room (POST /deposition/sessions)
    ↓
WebSocket connection established (WS /deposition/ws/{session_id})
    ↓
Attorney enters witness testimony (client-side)
    ↓
Frontend sends: {type: "testimony", text: "..."}
    ↓
deposition_agent.analyze_testimony()
    ├─ Match against evidence library
    ├─ Flag contradictions
    ├─ Identify relevant weapons
    └─ Check for perjury opportunities
    ↓
deposition_agent.suggest_follow_up_questions()
    ├─ Score by strategy type
    ├─ Rank by effectiveness
    └─ Return top 3 follow-ups
    ↓
WebSocket sends: {type: "suggestion", questions: [...], analysis: {...}}
    ↓
Frontend displays suggestions in real-time
    ↓
Attorney chooses question, enters next testimony
    ↓
Transcript accumulates in DepositionSession.transcript_text
    ↓
Attorney closes session (PATCH /close)
    ↓
Summary generated by deposition_agent.generate_summary()
```

### Low-Latency Requirements

- WebSocket message round-trip: < 200ms target
- Testimony analysis: < 50ms (keyword matching, not AI inference initially)
- Suggestion ranking: < 100ms
- Future Claude calls: < 2000ms (user acceptable for live deposition)

### Scaling Strategy

**Current (Single Case)**
- SQLite stored in-process
- Weapons and evidence cached in memory
- Single deposition session at a time
- Sufficient for 1-2 concurrent users

**Production Scale (10-100 attorneys)**
- PostgreSQL with connection pooling
- Redis for evidence cache + suggestion cache
- Multiple uvicorn workers behind nginx
- Message queue (Celery) for heavy Claude API calls
- Session affinity: each deposition → dedicated worker

## API Data Flow Examples

### Document Upload Flow

```
1. Client sends document file via multipart form
2. Backend extracts text (pdf2image, OCR if needed)
3. document_agent.extract_and_analyze()
   - Calculate SHA256 hash for integrity
   - Count characters
   - Match against COAs via keyword search
   - Extract key passages and burden element references
4. Store Document record with text_content, hash, metadata
5. Return {id, coa_matches: [{coa_name, match_strength}], key_passages: [...]}
6. Client displays matched COAs to attorney for review
```

### Weapon Deployment Flow

```
1. Attorney reviews weapon on WeaponDetail page
2. Attorney clicks "Deploy This Weapon"
3. Frontend calls POST /weapons/{id}/deploy
4. Backend sets weapon.status = "deployed"
5. Frontend navigates to DepositionRoom with this weapon loaded
6. Attorney reads question and asks in deposition
7. Witness testimony entered
8. deposition_agent identifies this weapon in follow-up suggestions
9. Testimony and weapon link stored in transcript
```

### What-If Simulation Flow

```
1. Attorney on WeaponDetail clicks "Simulate"
2. Frontend calls POST /weapons/{id}/simulate
3. opposition_agent.predict_defense_response(weapon)
   - Looks up weapon.strategy name in DEFENSE_RESPONSES map
   - Returns canned response (or generates based on evidence_score)
4. Frontend displays ResponseTree with 4 elements:
   - "David Says" (opposition's expected response)
   - "Your Counter" (attorney's next move)
   - "Delta" (effect/outcome)
   - "Perjury Evidence" (how this creates liability)
5. Attorney reads through tree, adjusts strategy if needed
6. Attorney can edit weapon.attorney_notes with findings
7. Saved via PATCH /weapons/{id}
```

## Security Considerations

1. **CORS:** Production should restrict origins (configured for * in dev)
2. **Authentication:** Future implementation needed (JWT tokens)
3. **Authorization:** Role-based access (Attorney, Paralegal, Admin)
4. **Data Encryption:** At-rest via PostgreSQL with TLS
5. **Audit Trail:** AttorneyEdit table tracks all weapon modifications
6. **Hash Verification:** Document SHA256 prevents tampering
7. **WebSocket Auth:** Session ID should be tied to case access
8. **Rate Limiting:** Future implementation to prevent abuse

## Deployment Strategy

### Development
```bash
# Local development with hot reload
cd backend && python main.py
cd frontend && npm run dev
```

### Docker Compose (Staging)
```bash
docker-compose up -d
# Exposes: http://localhost (nginx reverse proxy)
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

### Kubernetes (Production)
- FastAPI backend pod (replicas: 3)
- PostgreSQL pod (with persistent volume)
- Redis pod (caching)
- Nginx ingress controller
- HTTPS/TLS termination at ingress

## Cost Analysis (Estimated Monthly)

### Infrastructure
- AWS ECS/Fargate: $200-500 (3 FastAPI instances)
- PostgreSQL RDS: $100-300 (multi-AZ)
- Redis ElastiCache: $50-100
- ALB/NAT Gateway: $50-100
- S3 for document storage: $10-50 (100GB)
- **Subtotal: $410-1050/month**

### API Costs (Claude Integration Future)
- Claude Opus 4 calls:
  - Opposition simulation: ~50 calls/week × $0.015 = $30/month
  - Deposition suggestions: ~100 calls/week × $0.003 = $13/month
  - Document analysis: ~200 calls/month × $0.015 = $30/month
- **API Subtotal: ~$73/month per attorney**

### Storage & Transfer
- Document storage: $0.023/GB/month × 100GB = $2.30/month
- Data transfer: $0.09/GB × 500GB/month = $45/month
- **Storage Subtotal: ~$50/month**

### Total (10 attorneys)
- Infrastructure: $600/month
- API costs: $730/month (73 × 10)
- Storage: $50/month
- **Total: ~$1,380/month or ~$138/attorney/month**

With volume licensing and optimization, could reach $80-100/attorney/month.

## Future Roadmap

### Phase 1 (Current)
- Stub agents with canned responses
- SQLite database
- Basic WebSocket deposition room
- Manual weapon/strategy entry

### Phase 2 (Q2 2026)
- Claude API integration for opposition_agent
- Real-time deposition with Claude suggestions
- Document upload with automatic COA matching
- Attorney authentication & case access control

### Phase 3 (Q3 2026)
- Multi-case, multi-attorney support
- PostgreSQL migration
- Redis caching layer
- Advanced analytics (case strength, win probability)

### Phase 4 (Q4 2026)
- Complaint auto-generation from approved COAs
- Integration with document automation (Docassemble, etc.)
- Mobile app for deposition on iPad
- Voice transcription integration (Rev, Fireflies.ai)

## Implementation Checklist

- [ ] Backend main.py startup and routes
- [ ] Database initialization and seeding
- [ ] All 4 agents with basic implementation
- [ ] Frontend pages and components
- [ ] Docker containers and docker-compose
- [ ] WebSocket deposition room
- [ ] API testing and documentation
- [ ] Claude API integration hooks for future

## Testing Strategy

### Unit Tests
- Agent functions with mock inputs
- Schema validation
- Database model creation

### Integration Tests
- API endpoint round-trips
- Database transaction handling
- WebSocket message flow

### E2E Tests
- User journey: Upload document → View COAs → Deploy weapon → Simulate response
- Deposition room: Create session → Add testimony → Get suggestions → Close

### Performance Tests
- 100 concurrent deposition connections
- Response time under 200ms for suggestions
- Database queries < 50ms

## Monitoring & Logging

- FastAPI middleware logs all requests
- WebSocket connection/disconnection events
- Agent execution time tracking
- Database query performance
- Error rates and stack traces
- Attorney usage metrics (weapons deployed, deposition duration, etc.)
