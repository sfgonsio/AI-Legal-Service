# CaseCore - Legal Case Management & Strategy Platform

A comprehensive platform for attorneys to systematically build cases through evidence-based weapons, strategic planning, and real-time deposition assistance powered by AI.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)

### Development Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
# Server runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Dev server runs on http://localhost:5173
```

Access the application at `http://localhost:5173`

### Docker Setup

```bash
docker-compose up -d
# Access at http://localhost
```

The docker-compose file includes:
- FastAPI backend (port 8000)
- React frontend (port 5173)
- Nginx reverse proxy (port 80)

## Project Structure

```
production/
├── backend/                 # FastAPI application
│   ├── main.py             # FastAPI app entry point
│   ├── database.py         # SQLite async setup
│   ├── models.py           # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── seed_data.py        # Mills v. Polley case seed data
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile
│   ├── routes/
│   │   ├── cases.py        # Case CRUD
│   │   ├── weapons.py      # Weapon management & simulation
│   │   ├── strategies.py   # Strategy retrieval
│   │   ├── coas.py         # Cause of Action management
│   │   ├── documents.py    # Document management
│   │   └── deposition.py   # Deposition sessions & WebSocket
│   └── agents/
│       ├── opposition_agent.py      # Predict defense responses
│       ├── strategy_agent.py        # Recommend next weapons
│       ├── deposition_agent.py      # Real-time deposition analysis
│       └── document_agent.py        # Document analysis & COA matching
│
├── frontend/               # React application
│   ├── package.json
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── main.jsx        # React entry point
│   │   ├── App.jsx         # Router setup
│   │   ├── index.css       # Tailwind styles
│   │   ├── api/
│   │   │   └── client.js   # API wrapper with all endpoints
│   │   ├── hooks/
│   │   │   └── useWebSocket.js     # WebSocket hook for deposition
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Case overview & pipeline
│   │   │   ├── WeaponDetail.jsx    # Weapon detail with simulation
│   │   │   ├── StrategyView.jsx    # Strategy detail with weapons
│   │   │   └── DepositionRoom.jsx  # Real-time deposition assistant
│   │   └── components/
│   │       ├── BreadcrumbNav.jsx   # Navigation breadcrumbs
│   │       ├── CaseStrengthMeter.jsx  # Progress bar
│   │       ├── AttorneyNotes.jsx   # Editable notes field
│   │       ├── ResponseTree.jsx    # Expandable response tree
│   │       └── SourceFileViewer.jsx # Document viewer
│   └── Dockerfile
│
├── docker-compose.yml      # Multi-container orchestration
├── nginx.conf             # Reverse proxy config
├── ARCHITECTURE.md        # Comprehensive architecture documentation
└── README.md             # This file
```

## Key Features

### 1. Case Management
- Create and manage legal cases
- Track case metadata (plaintiff, defendant, court)
- Monitor case status and pipeline progress

### 2. Weapons Arsenal (26 for Mills v. Polley)
- **Weapons** are precision deposition questions designed to:
  - Strengthen plaintiff's position
  - Weaken defendant's story
  - Create perjury trap opportunities
- Each weapon has:
  - Evidence score (0-100)
  - Associated CACI jury instruction reference
  - Predicted opposition response
  - Strategic rationale

### 3. What-If Simulation
- Simulate opposition responses to any weapon
- Built-in response library with tactics:
  - David's likely objection/response
  - Your counter-point
  - Delta (effect on case)
  - Perjury evidence flags

### 4. Strategic Planning
- **5 Strategies** orchestrate weapons:
  - Document Pincer: Use documents to create logical trap
  - Admissions Cascade: Lock in admissions progressively
  - Timeline Trap: Establish impossible timeline
  - Entity Shell Game: Expose hidden corporate structure
  - Financial Impossibility: Show fund sources don't add up
- Each strategy has:
  - Value score
  - Deposition impact
  - Trial impact
  - Execution phases

### 5. Causes of Action (COAs)
- 12 COAs with CACI jury instruction references
- Burden elements for each COA
- Evidence tracking and strength scoring
- Attorney approval workflow

### 6. Document Management
- Upload evidence (PDFs, emails, documents)
- Automatic text extraction
- SHA256 integrity hashing
- COA relevance scoring
- Key passage extraction

### 7. Real-Time Deposition Assistant
- WebSocket-based live connection
- Attorney enters witness testimony
- AI suggests follow-up questions in real-time
- Contradiction detection against evidence
- Perjury trap opportunity flags
- Accumulating transcript

### 8. Perjury Paths
- 4 sophisticated perjury traps:
  - Financial Trap
  - Entity Shell Game
  - Concealment Chain
  - Timeline Destroy
- Shows how weapons spring each trap

## API Documentation

### Core Endpoints

**Cases**
```
POST   /cases              Create case
GET    /cases              List all cases
GET    /cases/{id}         Get case detail
PATCH  /cases/{id}         Update case
DELETE /cases/{id}         Delete case
```

**Weapons**
```
GET    /weapons?case_id=1  List weapons
GET    /weapons/1          Get weapon detail
PATCH  /weapons/1          Update weapon (attorney edits)
POST   /weapons/1/simulate Simulate opposition response
POST   /weapons/1/deploy   Mark weapon as deployed
```

**Strategies**
```
GET    /strategies?case_id=1   List strategies
GET    /strategies/1           Get strategy detail
```

**COAs**
```
GET    /coas?case_id=1     List COAs
GET    /coas/1             Get COA with burden elements
```

**Documents**
```
GET    /documents?case_id=1    List documents
GET    /documents/1            Get document with text
```

**Deposition (WebSocket)**
```
POST   /deposition/sessions            Create session
GET    /deposition/sessions/{id}       Get session
GET    /deposition/sessions/case/{id}  List case sessions
WS     /deposition/ws/{session_id}     Real-time feed

WebSocket Message Format:
  IN:  {"type": "testimony", "text": "witness statement", "witness_name": "John Doe"}
  OUT: {"type": "suggestion", "follow_up_questions": [...], "analysis": {...}}
```

Complete API documentation available at `http://localhost:8000/docs` when running backend.

## Database

### SQLite (Development)
- File-based: `./casecore.db`
- Async driver: aiosqlite
- Auto-initialized on startup

### Schema
- Cases, Documents, COAs, BurdenElements
- Weapons, Strategies, PerjuryPaths
- DepositionSessions, AttorneyEdits
- See ARCHITECTURE.md for full schema documentation

### Seeding
Backend automatically seeds Mills v. Polley case on startup:
- 1 case
- 26 weapons (fully configured)
- 5 strategies
- 4 perjury paths
- 12 COAs
- 9 source documents

## Configuration

### Environment Variables

**Backend**
```
DATABASE_URL=sqlite+aiosqlite:///./casecore.db
PYTHONUNBUFFERED=1
```

**Frontend**
```
VITE_API_URL=http://localhost:8000
```

### Database Migration (SQLite → PostgreSQL)
Future migration documented in ARCHITECTURE.md. Current implementation:
```python
# Change DATABASE_URL to:
DATABASE_URL=postgresql+asyncpg://user:password@localhost/casecore
# Install: pip install asyncpg psycopg2-binary
```

## Development Workflow

### Adding a New Weapon

1. Edit `backend/seed_data.py`:
```python
{
    "id": 27,
    "category": "WEAPONIZE",
    "coa": "Fraud",
    "caci": "CACI 1900",
    "strategy": "Your Strategy Name",
    "question": "What exactly did you mean when you said...?",
    "evidence_score": 85.0,
    "perjury_trap": True
}
```

2. Restart backend to re-seed

### Adding Opposition Response

Edit `backend/agents/opposition_agent.py`:
```python
DEFENSE_RESPONSES = {
    "Your Strategy Name": {
        "david_says": "...",
        "counter": "...",
        "delta": "...",
        "perjury_evidence": "..."
    }
}
```

### Modifying Frontend UI

All pages in `frontend/src/pages/` and components in `frontend/src/components/` are editable without rebuilding. Vite handles hot module reload.

## Testing

### Manual Testing Checklist

- [ ] Create new case
- [ ] List all cases
- [ ] View case detail (Dashboard)
- [ ] View weapon detail
- [ ] Simulate weapon response
- [ ] Update attorney notes
- [ ] View strategy with weapons
- [ ] Create deposition session
- [ ] Add testimony and get suggestions
- [ ] Close deposition session

### API Testing

```bash
# Get all cases
curl http://localhost:8000/cases

# Get case 1
curl http://localhost:8000/cases/1

# Simulate weapon 1
curl -X POST http://localhost:8000/weapons/1/simulate

# See all endpoints
curl http://localhost:8000/docs
```

## AI Agent Architecture

### Current Implementation (Stubs)
1. **opposition_agent:** Canned responses keyed by strategy name
2. **strategy_agent:** Scoring-based weapon recommendations
3. **deposition_agent:** Keyword matching for testimony analysis
4. **document_agent:** Simple text extraction and COA matching

### Future Integration (Claude API)
Each agent has clearly marked integration points for Claude Opus 4:
- Dynamic opposition response generation
- Intelligent weapon sequencing
- Real-time live deposition suggestions
- Semantic document analysis

See ARCHITECTURE.md for detailed integration roadmap.

## Deployment

### Docker Compose (Recommended for Dev/Staging)
```bash
docker-compose up -d
# Access: http://localhost
```

### Kubernetes (Production)
- See ARCHITECTURE.md for K8s configuration
- Helm chart template available in `helm/` (create as needed)

### Environment-Specific Configs
```bash
# Development
docker-compose -f docker-compose.yml up

# Staging
docker-compose -f docker-compose.staging.yml up

# Production
docker-compose -f docker-compose.prod.yml up
```

## Security

- [ ] Add JWT authentication
- [ ] Implement RBAC (Attorney, Paralegal, Admin)
- [ ] Add HTTPS/TLS (Nginx ingress)
- [ ] Rate limiting on API endpoints
- [ ] Audit logging for sensitive operations
- [ ] Document encryption at rest

See ARCHITECTURE.md Security Considerations section.

## Performance

### Benchmarks (Target)
- API response time: < 100ms (p95)
- WebSocket suggestion latency: < 200ms (p95)
- Database query: < 50ms (p95)
- Frontend interaction response: < 16ms (60fps)

### Monitoring
- Log all API requests
- Track WebSocket connection metrics
- Monitor database query performance
- Alert on error rates > 1%

## Troubleshooting

**Backend won't start:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Install dependencies
pip install -r backend/requirements.txt

# Check for port conflicts
lsof -i :8000
```

**Frontend not loading:**
```bash
# Check Node version
node --version  # Should be 20+

# Clear node_modules and reinstall
rm -rf frontend/node_modules frontend/package-lock.json
cd frontend && npm install
```

**WebSocket connection fails:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check WebSocket URL matches session ID
# Browser console should show connection logs
```

**Database issues:**
```bash
# Remove corrupted database
rm casecore.db

# Restart backend to re-seed
# Or manually seed:
python backend/seed_data.py
```

## Contributing

### Code Style
- Python: Follow PEP 8
- JavaScript: Use Prettier/ESLint
- SQL: Use meaningful table/column names
- Component names: PascalCase
- Function names: camelCase

### Git Workflow
```bash
git checkout -b feature/weapon-simulation
# ... make changes ...
git commit -m "feat: add what-if weapon simulation"
git push origin feature/weapon-simulation
# Create pull request
```

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Enhancement
- [ ] Documentation

## Testing
- [ ] Manual testing
- [ ] Unit tests added
- [ ] Integration tests added

## Checklist
- [ ] Code follows style guidelines
- [ ] Comments added for complex logic
- [ ] Documentation updated
```

## Support & Contact

For issues, feature requests, or questions:
1. Check ARCHITECTURE.md for technical details
2. Review API docs at `/docs` endpoint
3. Check browser console for client errors
4. Check server logs for backend errors

## License

Internal Use Only - Anthropic Legal Services

## Roadmap

### Phase 1 (Current - Q1 2026)
- ✅ Backend scaffold with agents
- ✅ Frontend pages and components
- ✅ Mills v. Polley case seed data
- ✅ What-if weapon simulation
- ✅ Real-time deposition WebSocket
- [ ] Claude API integration hooks

### Phase 2 (Q2 2026)
- [ ] Claude Opus 4 opposition agent
- [ ] Document auto-COA matching
- [ ] Attorney authentication
- [ ] Multi-case support

### Phase 3 (Q3 2026)
- [ ] PostgreSQL migration
- [ ] Redis caching
- [ ] Mobile deposition app
- [ ] Case analytics dashboard

### Phase 4 (Q4 2026)
- [ ] Complaint auto-generation
- [ ] Integration with Docassemble
- [ ] Voice transcription (Fireflies.ai)
- [ ] Advanced win probability modeling

## Changelog

### v1.0.0 (Initial Release)
- Basic case and weapon management
- Weapon simulation with opposition responses
- Real-time deposition room with WebSocket
- Strategic planning with 5 core strategies
- Mills v. Polley case pre-loaded with 26 weapons
- Dark theme responsive UI

---

**Built with:** FastAPI, SQLAlchemy, React, Tailwind CSS, WebSocket
**Architecture:** Real-time deposition-driven design
**Team:** Anthropic Legal Services Division
