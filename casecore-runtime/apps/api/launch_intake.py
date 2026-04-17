"""
INTAKE_ENGINE Quick Launch Script

Starts the full INTAKE_ENGINE with:
  - FastAPI server on http://localhost:8000
  - Interactive API docs at http://localhost:8000/docs
  - INTERVIEW_AGENT (Anthropic Claude)
  - COA Engine (CACI + EVID authority store)
  - Whisper Audio Transcription (OpenAI)
  - Evidence Ingestion Pipeline

Prerequisites:
  pip install fastapi uvicorn anthropic openai python-dotenv pypdf python-multipart
  cp .env.template .env   # then fill in API keys

Usage:
  python launch_intake.py

Then open: http://localhost:8000/docs
Or open:   http://localhost:8000/intake-demo  (interactive demo UI)
"""

import os
import sys

# Load .env if present
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"[OK] Loaded .env from {env_path}")
    else:
        print(f"[WARN] No .env file found. Copy .env.template to .env and add your API keys.")
except ImportError:
    print("[WARN] python-dotenv not installed. Set env vars manually or: pip install python-dotenv")

# Validate API keys
anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
openai_key = os.getenv("OPENAI_API_KEY", "")

if not anthropic_key or anthropic_key.startswith("sk-ant-xxx"):
    print("[WARN] ANTHROPIC_API_KEY not set. INTERVIEW_AGENT will use fallback questions.")
if not openai_key or openai_key.startswith("sk-xxx"):
    print("[WARN] OPENAI_API_KEY not set. Audio transcription will be unavailable.")

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Import routers
from src.routers.intake import router as intake_router
from src.routers.files import router as files_router
from src.routers.auth import router as auth_router
from src.routers.streaming import router as streaming_router
from src.routers.cloud_storage import router as cloud_storage_router
from src.routers.bulk_import import router as bulk_import_router
from src.config import settings

# Create app
app = FastAPI(
    title="CASECORE INTAKE_ENGINE",
    description="AI-Powered Legal Intake System — Narrative → COA → Burden → Evidence",
    version="2.0.0",
)

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(intake_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(streaming_router, prefix="/api/v1")
app.include_router(cloud_storage_router, prefix="/api/v1")
app.include_router(bulk_import_router, prefix="/api/v1")

# Serve static files (enhanced UI)
from fastapi.staticfiles import StaticFiles
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "engine": "INTAKE_ENGINE v2",
        "anthropic_configured": bool(anthropic_key and not anthropic_key.startswith("sk-ant-xxx")),
        "openai_configured": bool(openai_key and not openai_key.startswith("sk-xxx")),
    }


# ---------------------------------------------------------------------------
# Interactive Demo UI
# ---------------------------------------------------------------------------

DEMO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CaseCore INTAKE_ENGINE Demo</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }
  .container { max-width: 1400px; margin: 0 auto; }
  h1 { font-size: 1.5rem; color: #38bdf8; margin-bottom: 4px; }
  .subtitle { color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
  .card { background: #1e293b; border-radius: 12px; padding: 16px; border: 1px solid #334155; }
  .card h2 { font-size: 1rem; color: #38bdf8; margin-bottom: 12px; }
  .card h3 { font-size: 0.85rem; color: #94a3b8; margin: 12px 0 6px; }
  textarea { width: 100%; height: 160px; background: #0f172a; color: #e2e8f0; border: 1px solid #475569; border-radius: 8px; padding: 10px; font-size: 0.85rem; resize: vertical; font-family: inherit; }
  input[type=text] { width: 100%; background: #0f172a; color: #e2e8f0; border: 1px solid #475569; border-radius: 6px; padding: 8px; font-size: 0.85rem; margin-bottom: 8px; }
  button { background: #2563eb; color: white; border: none; border-radius: 6px; padding: 8px 16px; cursor: pointer; font-size: 0.85rem; margin: 4px 4px 4px 0; }
  button:hover { background: #3b82f6; }
  button:disabled { background: #475569; cursor: not-allowed; }
  button.secondary { background: #334155; }
  button.secondary:hover { background: #475569; }
  button.danger { background: #dc2626; }
  .status { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
  .status.green { background: #166534; color: #86efac; }
  .status.yellow { background: #854d0e; color: #fde047; }
  .status.red { background: #991b1b; color: #fca5a5; }
  .status.blue { background: #1e40af; color: #93c5fd; }
  .questions-list { list-style: none; padding: 0; }
  .questions-list li { background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 8px; margin-bottom: 6px; font-size: 0.82rem; cursor: pointer; }
  .questions-list li:hover { border-color: #38bdf8; }
  .coa-card { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px; margin-bottom: 8px; }
  .coa-name { font-weight: 600; color: #f8fafc; }
  .element-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 0.8rem; border-bottom: 1px solid #1e293b; }
  .bar { height: 6px; border-radius: 3px; background: #334155; margin-top: 6px; }
  .bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
  .log { background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 8px; font-family: monospace; font-size: 0.75rem; max-height: 200px; overflow-y: auto; white-space: pre-wrap; color: #94a3b8; }
  .kpi-row { display: flex; gap: 8px; margin-bottom: 12px; }
  .kpi { flex: 1; background: #0f172a; border-radius: 8px; padding: 10px; text-align: center; }
  .kpi .value { font-size: 1.5rem; font-weight: 700; color: #38bdf8; }
  .kpi .label { font-size: 0.7rem; color: #94a3b8; }
  .recording { animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
  #chat-messages { max-height: 300px; overflow-y: auto; }
  .msg { padding: 6px 10px; margin: 4px 0; border-radius: 8px; font-size: 0.82rem; }
  .msg.agent { background: #1e3a5f; border: 1px solid #2563eb; }
  .msg.client { background: #1e293b; border: 1px solid #475569; }
  .msg .role { font-size: 0.7rem; color: #94a3b8; margin-bottom: 2px; }
</style>
</head>
<body>
<div class="container">
  <h1>CaseCore INTAKE_ENGINE</h1>
  <p class="subtitle">AI-Powered Legal Intake: Narrative &rarr; COA &rarr; Burden Elements &rarr; Targeted Questions &rarr; Evidence Mapping</p>

  <div class="kpi-row">
    <div class="kpi"><div class="value" id="kpi-status">READY</div><div class="label">Engine Status</div></div>
    <div class="kpi"><div class="value" id="kpi-coas">0</div><div class="label">Candidate COAs</div></div>
    <div class="kpi"><div class="value" id="kpi-elements">0/0</div><div class="label">Elements Proven</div></div>
    <div class="kpi"><div class="value" id="kpi-evidence">0</div><div class="label">Evidence Files</div></div>
    <div class="kpi"><div class="value" id="kpi-gaps">0</div><div class="label">Open Gaps</div></div>
  </div>

  <div class="grid">
    <!-- Column 1: Intake -->
    <div class="card">
      <h2>1. Client Narrative Intake</h2>
      <div style="margin-bottom:8px">
        <input type="text" id="case-id" placeholder="Case ID (auto-generated)" />
        <input type="text" id="client-name" placeholder="Client name (optional)" />
      </div>
      <textarea id="narrative" placeholder="Paste or type the client's narrative here...&#10;&#10;Example: My employer terminated me on March 15, 2026 after I reported safety violations to OSHA. I had worked there for 6 years with excellent reviews. Two weeks before my termination, I filed a complaint with the California Division of Occupational Safety..."></textarea>
      <div style="margin-top:8px">
        <button id="btn-start" onclick="startIntake()">Start Intake</button>
        <button class="secondary" id="btn-record" onclick="toggleRecording()">Record Audio</button>
        <label style="font-size:0.8rem;color:#94a3b8;margin-left:8px">
          <input type="file" id="audio-upload" accept="audio/*,video/*" style="display:none" onchange="uploadAudio(this)">
          <button class="secondary" onclick="document.getElementById('audio-upload').click()">Upload Audio/Video</button>
        </label>
      </div>
    </div>

    <!-- Column 2: Interview -->
    <div class="card">
      <h2>2. Interview Session</h2>
      <div id="chat-messages"></div>
      <h3>Suggested Questions</h3>
      <ul class="questions-list" id="questions-list">
        <li style="color:#64748b">Start an intake to see AI-generated questions...</li>
      </ul>
      <div style="margin-top:8px">
        <textarea id="response-input" style="height:60px" placeholder="Type client/attorney response..."></textarea>
        <button id="btn-respond" onclick="submitResponse()" disabled>Send Response</button>
        <label style="font-size:0.8rem;color:#94a3b8;margin-left:4px">
          <input type="file" id="evidence-upload" accept="*/*" style="display:none" onchange="uploadEvidence(this)">
          <button class="secondary" onclick="document.getElementById('evidence-upload').click()">Attach Evidence</button>
        </label>
      </div>
    </div>

    <!-- Column 3: COA + Burden Scorecard -->
    <div class="card">
      <h2>3. COA &amp; Burden Scorecard</h2>
      <div id="coa-container">
        <p style="color:#64748b;font-size:0.82rem">COAs will appear here after intake starts...</p>
      </div>
      <h3>Audit Log</h3>
      <div class="log" id="audit-log">Waiting for intake...\n</div>
      <div style="margin-top:8px">
        <button class="danger" id="btn-complete" onclick="completeIntake()" disabled>Complete Intake</button>
      </div>
    </div>
  </div>
</div>

<script>
const API = '/api/v1';
let state = { caseId: null, sessionId: null, intakeId: null, recording: false, mediaRecorder: null };

function log(msg) {
  const el = document.getElementById('audit-log');
  const ts = new Date().toLocaleTimeString();
  el.textContent += `[${ts}] ${msg}\\n`;
  el.scrollTop = el.scrollHeight;
}

function addMessage(role, content) {
  const el = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `<div class="role">${role.toUpperCase()}</div>${content}`;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}

function updateQuestions(questions) {
  const el = document.getElementById('questions-list');
  el.innerHTML = '';
  (questions || []).forEach(q => {
    const li = document.createElement('li');
    li.textContent = q;
    li.onclick = () => { document.getElementById('response-input').value = ''; addMessage('agent', q); };
    el.appendChild(li);
  });
}

function updateScorecard(data) {
  if (!data || !data.scorecard) return;
  const container = document.getElementById('coa-container');
  container.innerHTML = '';
  let totalEl = 0, provenEl = 0;
  (data.scorecard.coas || []).forEach(coa => {
    totalEl += coa.elements_total;
    provenEl += coa.elements_proven;
    const pct = coa.coverage_pct || 0;
    const color = pct >= 70 ? '#22c55e' : pct >= 40 ? '#eab308' : '#ef4444';
    container.innerHTML += `
      <div class="coa-card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span class="coa-name">${coa.name}</span>
          <span class="status ${coa.status === 'strong' ? 'green' : coa.status === 'viable' ? 'yellow' : 'red'}">${coa.status}</span>
        </div>
        <div style="font-size:0.75rem;color:#94a3b8;margin:4px 0">${coa.elements_proven}/${coa.elements_total} elements | ${coa.coverage_pct}% coverage</div>
        <div class="bar"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
        <div style="font-size:0.75rem;color:#64748b;margin-top:4px">${coa.remedies_count} remedies available</div>
      </div>`;
  });
  document.getElementById('kpi-coas').textContent = data.scorecard.coas?.length || 0;
  document.getElementById('kpi-elements').textContent = `${provenEl}/${totalEl}`;
}

async function startIntake() {
  const narrative = document.getElementById('narrative').value.trim();
  if (!narrative) return alert('Enter a narrative first');

  state.caseId = document.getElementById('case-id').value || 'CASE-' + Date.now();
  document.getElementById('case-id').value = state.caseId;
  document.getElementById('btn-start').disabled = true;
  document.getElementById('kpi-status').textContent = 'PROCESSING';
  log('Starting intake for ' + state.caseId);

  try {
    const res = await fetch(`${API}/cases/${state.caseId}/intake/start`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        narrative,
        client_name: document.getElementById('client-name').value || null,
        case_type_hint: null,
        jurisdiction_hint: 'California',
      })
    });
    const data = await res.json();
    state.sessionId = data.interview_session_id;
    state.intakeId = data.intake?.intake_id;

    document.getElementById('kpi-status').textContent = data.intake?.status || 'ACTIVE';
    document.getElementById('btn-respond').disabled = false;
    document.getElementById('btn-complete').disabled = false;

    addMessage('client', narrative.substring(0, 200) + (narrative.length > 200 ? '...' : ''));
    log('Intake started: ' + data.intake?.status);
    log('Structured model: ' + (data.intake?.structured_model?.parties?.length || 0) + ' parties, ' + (data.intake?.structured_model?.events?.length || 0) + ' events');

    updateQuestions(data.initial_questions);
    document.getElementById('kpi-gaps').textContent = data.intake?.gap_summary?.total_gaps || 0;

    // Fetch COA scorecard
    try {
      const coaRes = await fetch(`${API}/cases/${state.caseId}/intake/coa`);
      if (coaRes.ok) {
        const coaData = await coaRes.json();
        updateScorecard(coaData);
        log('COA assessment: ' + (coaData.scorecard?.coas?.length || 0) + ' causes of action identified');
      }
    } catch(e) { log('COA fetch: ' + e.message); }

  } catch(e) {
    log('ERROR: ' + e.message);
    document.getElementById('kpi-status').textContent = 'ERROR';
  }
  document.getElementById('btn-start').disabled = false;
}

async function submitResponse() {
  const msg = document.getElementById('response-input').value.trim();
  if (!msg || !state.sessionId) return;

  addMessage('client', msg);
  document.getElementById('response-input').value = '';
  log('Client response submitted');

  try {
    const res = await fetch(`${API}/cases/${state.caseId}/intake/respond`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ session_id: state.sessionId, message: msg, role: 'client' })
    });
    const data = await res.json();

    document.getElementById('kpi-status').textContent = data.intake?.status || 'ACTIVE';
    document.getElementById('kpi-gaps').textContent = data.intake?.gap_summary?.total_gaps || 0;
    log(`Refined: +${data.new_gaps_detected} new gaps, ${data.gaps_resolved} resolved`);

    updateQuestions(data.follow_up_questions);
    if (data.follow_up_questions?.length) {
      addMessage('agent', data.follow_up_questions[0]);
    }

    // Refresh COA scorecard
    const coaRes = await fetch(`${API}/cases/${state.caseId}/intake/coa`);
    if (coaRes.ok) updateScorecard(await coaRes.json());

  } catch(e) { log('ERROR: ' + e.message); }
}

async function uploadEvidence(input) {
  if (!input.files[0] || !state.caseId) return;
  const formData = new FormData();
  formData.append('file', input.files[0]);
  formData.append('actor', 'client');

  log('Uploading evidence: ' + input.files[0].name);
  try {
    const res = await fetch(`${API}/cases/${state.caseId}/intake/evidence`, { method: 'POST', body: formData });
    const data = await res.json();
    const ps = data.pipeline_summary || {};
    log(`Evidence ingested: ${ps.type_detected} | ${ps.text_length} chars extracted | ${ps.burden_elements_mapped} elements mapped | Hash: ${ps.hash?.substring(0,16)}...`);
    document.getElementById('kpi-evidence').textContent = parseInt(document.getElementById('kpi-evidence').textContent) + 1;
    addMessage('agent', `Evidence received: ${input.files[0].name} (${ps.type_detected}). ${ps.burden_elements_mapped} burden elements matched.`);

    if (data.coa_scorecard) updateScorecard(data);
  } catch(e) { log('ERROR: ' + e.message); }
  input.value = '';
}

async function uploadAudio(input) {
  if (!input.files[0]) return;
  const caseId = state.caseId || ('CASE-' + Date.now());
  if (!state.caseId) { state.caseId = caseId; document.getElementById('case-id').value = caseId; }

  const formData = new FormData();
  formData.append('audio', input.files[0]);
  formData.append('speaker', 'client');

  log('Transcribing audio: ' + input.files[0].name);
  document.getElementById('kpi-status').textContent = 'TRANSCRIBING';

  try {
    const res = await fetch(`${API}/cases/${caseId}/intake/audio`, { method: 'POST', body: formData });
    const data = await res.json();

    if (data.transcript?.full_text) {
      addMessage('client', '[Audio transcript] ' + data.transcript.full_text.substring(0, 300) + '...');
      log('Transcription complete: ' + data.transcript.duration_seconds + 's');
    }

    state.sessionId = data.interview_session_id || state.sessionId;
    document.getElementById('kpi-status').textContent = data.intake?.status || 'ACTIVE';
    document.getElementById('btn-respond').disabled = false;
    document.getElementById('btn-complete').disabled = false;

    updateQuestions(data.follow_up_questions);
  } catch(e) { log('ERROR: ' + e.message); }
  input.value = '';
}

function toggleRecording() {
  const btn = document.getElementById('btn-record');
  if (!state.recording) {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      state.mediaRecorder = new MediaRecorder(stream);
      const chunks = [];
      state.mediaRecorder.ondataavailable = e => chunks.push(e.data);
      state.mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const file = new File([blob], 'recording.webm', { type: 'audio/webm' });
        const dt = new DataTransfer();
        dt.items.add(file);
        document.getElementById('audio-upload').files = dt.files;
        uploadAudio(document.getElementById('audio-upload'));
        stream.getTracks().forEach(t => t.stop());
      };
      state.mediaRecorder.start();
      state.recording = true;
      btn.textContent = 'Stop Recording';
      btn.classList.add('recording');
      btn.style.background = '#dc2626';
      log('Recording started...');
    }).catch(e => log('Microphone access denied: ' + e.message));
  } else {
    state.mediaRecorder.stop();
    state.recording = false;
    btn.textContent = 'Record Audio';
    btn.classList.remove('recording');
    btn.style.background = '';
    log('Recording stopped, transcribing...');
  }
}

async function completeIntake() {
  if (!state.caseId) return;
  try {
    const res = await fetch(`${API}/cases/${state.caseId}/intake/complete`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ force_complete: false })
    });
    const data = await res.json();
    document.getElementById('kpi-status').textContent = data.intake?.status || 'COMPLETE';
    log('Intake ' + (data.intake?.status || 'completed') + ': ' + (data.warnings?.join(', ') || 'no warnings'));
    if (data.unresolved_gaps > 0) {
      log(`WARNING: ${data.unresolved_gaps} unresolved gaps remain`);
    }
  } catch(e) { log('ERROR: ' + e.message); }
}

// Keyboard shortcut: Enter in response box
document.getElementById('response-input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitResponse(); }
});
</script>
</body>
</html>
"""


@app.get("/intake-demo", response_class=HTMLResponse)
def intake_demo():
    """Interactive demo UI for the INTAKE_ENGINE (original)."""
    return DEMO_HTML


@app.get("/intake", response_class=HTMLResponse)
def intake_ui():
    """Enhanced Intake UI — combined view (legacy, use /client or /attorney instead)."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "intake_ui.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>UI not found</h1>", status_code=404)


@app.get("/prospective", response_class=HTMLResponse)
def prospective_intake():
    """Prospective Client Intake — interview only, no evidence, no legal theory."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "prospective_intake.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Prospective Client UI not found</h1>", status_code=404)


@app.get("/new-client", response_class=HTMLResponse)
def new_client_intake():
    """New Client Intake — full 3-part flow (Interview + Evidence + Actors)."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "new_client_intake.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>New Client UI not found</h1>", status_code=404)


@app.get("/client", response_class=HTMLResponse)
def client_dashboard():
    """Existing Client Dashboard — case status, documents, messaging."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "client_intake.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Client Dashboard not found</h1>", status_code=404)


@app.get("/attorney", response_class=HTMLResponse)
def attorney_dashboard():
    """Attorney Dashboard — COA analysis, burden tracking, evidence, gaps."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "attorney_dashboard.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Attorney UI not found</h1>", status_code=404)


@app.get("/cloud-import", response_class=HTMLResponse)
def cloud_import():
    """Cloud Evidence Import — browse Dropbox, select files, one-click import."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "cloud_import.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Cloud Import page not found</h1>", status_code=404)


@app.get("/case-intake", response_class=HTMLResponse)
def case_intake():
    """Case Evidence Intake — upload documents, spreadsheets, emails, run analysis."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "case_intake.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Case Intake page not found</h1>", status_code=404)


@app.get("/attorney/dashboard", response_class=HTMLResponse)
def attorney_dashboard_full():
    """Attorney Case Dashboard — COA scorecard, evidence map, burden coverage."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "attorney_dashboard.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Attorney Dashboard not found</h1>", status_code=404)


@app.get("/coa-dashboard", response_class=HTMLResponse)
def coa_dashboard():
    """COA Analysis Dashboard — Full legal authority analysis results with burden mapping."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "coa_dashboard.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>COA Dashboard not found</h1>", status_code=404)


@app.get("/", response_class=HTMLResponse)
def login_page():
    """Login page — Existing Clients + Attorneys only. DEV mode has role passthrough."""
    ui_path = os.path.join(os.path.dirname(__file__), "static", "login.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Login page not found</h1>", status_code=404)



# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CASECORE INTAKE_ENGINE v2.1")
    print("  AI-Powered Legal Intake System")
    print("=" * 60)
    print(f"\n  Login:          http://localhost:8000/")
    print(f"  COA Dashboard:  http://localhost:8000/coa-dashboard    ** COA ANALYSIS RESULTS **")
    print(f"  Case Intake:    http://localhost:8000/case-intake     ** UPLOAD FILES HERE **")
    print(f"  Attorney Dash:  http://localhost:8000/attorney/dashboard")
    print(f"  Cloud Import:   http://localhost:8000/cloud-import")
    print(f"  Prospective:    http://localhost:8000/prospective")
    print(f"  New Client:     http://localhost:8000/new-client")
    print(f"  Client Dash:    http://localhost:8000/client")
    print(f"  Attorney:       http://localhost:8000/attorney")
    print(f"  API Docs:       http://localhost:8000/docs")
    print(f"  Health:         http://localhost:8000/health")
    print(f"\n  Anthropic: {'configured' if anthropic_key and not anthropic_key.startswith('sk-ant-xxx') else 'NOT SET'}")
    print(f"  OpenAI:    {'configured' if openai_key and not openai_key.startswith('sk-xxx') else 'NOT SET'}")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
