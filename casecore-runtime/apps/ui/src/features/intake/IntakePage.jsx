import React, { useMemo, useState } from "react";

const seedFacts = [
  {
    id: "F-001",
    statement: "Client states there was an oral agreement modifying payment timing.",
    status: "needs evidence",
    actor: "Client",
    impact: "High"
  },
  {
    id: "F-002",
    statement: "Opposing party allegedly continued accepting performance after the dispute began.",
    status: "strategic",
    actor: "Opposition",
    impact: "High"
  },
  {
    id: "F-003",
    statement: "A key event date is still ambiguous across the current intake narrative.",
    status: "gap",
    actor: "System",
    impact: "Medium"
  }
];

const seedEvidence = [
  { id: "E-014", label: "Email chain discussing payment timing", type: "Email", linkState: "linked" },
  { id: "E-021", label: "Invoice and delivery support", type: "Financial", linkState: "candidate" },
  { id: "E-033", label: "Text screenshots from client device", type: "Message", linkState: "unreviewed" }
];

export default function IntakePage() {
  const [narrative, setNarrative] = useState(
    "Client intake begins as a structured narrative build, not a passive form. The attorney and client should be able to shape claims, events, actors, dates, disputes, and evidence from this workspace."
  );
  const [facts, setFacts] = useState(seedFacts);

  const metrics = useMemo(() => {
    const highImpact = facts.filter((f) => f.impact === "High").length;
    const openGaps = facts.filter((f) => f.status === "gap" || f.status === "needs evidence").length;
    return {
      facts: facts.length,
      highImpact,
      openGaps
    };
  }, [facts]);

  function addFact(status) {
    const next = {
      id: `F-00${facts.length + 1}`,
      statement: `New ${status} fact object awaiting attorney refinement.`,
      status,
      actor: "Attorney",
      impact: "Medium"
    };
    setFacts([next, ...facts]);
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Phase I · Intake War Room</h1>
          <p className="page-subtitle">
            Intake is the front door to the litigation system. This workspace should help the attorney
            and client construct a usable legal narrative, extract facts, expose gaps, and begin linking
            evidence immediately.
          </p>
        </div>
        <div className="badge-row">
          <div className="badge">Action-first UI</div>
          <div className="badge">Fact objects</div>
          <div className="badge">Evidence-linked intake</div>
        </div>
      </div>

      <div className="kpi" style={{ marginBottom: 16 }}>
        <div className="card">
          <div className="item-meta">Fact objects</div>
          <div className="card-value">{metrics.facts}</div>
        </div>
        <div className="card">
          <div className="item-meta">High-value issues</div>
          <div className="card-value">{metrics.highImpact}</div>
        </div>
        <div className="card">
          <div className="item-meta">Open gaps / proof needs</div>
          <div className="card-value">{metrics.openGaps}</div>
        </div>
      </div>

      <div className="grid grid-3">
        <section className="card">
          <h3>Narrative Construction Canvas</h3>
          <p>
            Replace long forms with a narrative builder the attorney can shape, challenge, and lock into
            structured legal objects.
          </p>
          <div className="toolbar">
            <button className="btn btn-primary">Extract facts</button>
            <button className="btn">Mark disputed</button>
            <button className="btn">Attach evidence</button>
          </div>
          <textarea value={narrative} onChange={(e) => setNarrative(e.target.value)} />
        </section>

        <section className="card">
          <h3>Fact Object Stack</h3>
          <p>
            Facts should become discrete objects with IDs, status, actor ownership, and strategic value.
          </p>
          <div className="toolbar">
            <button className="btn btn-primary" onClick={() => addFact("strategic")}>Add strategic fact</button>
            <button className="btn" onClick={() => addFact("gap")}>Add gap</button>
            <button className="btn" onClick={() => addFact("needs evidence")}>Add proof need</button>
          </div>
          <div className="list">
            {facts.map((fact) => (
              <div className="item" key={fact.id}>
                <div className="item-title">
                  <span>{fact.id}</span>
                  <span className={`pill ${fact.status === "gap" ? "warning" : fact.status === "needs evidence" ? "danger" : "good"}`}>
                    {fact.status}
                  </span>
                </div>
                <div style={{ marginBottom: 8 }}>{fact.statement}</div>
                <div className="item-meta">Actor: {fact.actor} · Impact: {fact.impact}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="card">
          <h3>Intake Intelligence</h3>
          <p>
            Even at intake, the system should identify contradiction risk, proof gaps, timeline ambiguity,
            and next-step questioning opportunities.
          </p>

          <div className="list" style={{ marginBottom: 14 }}>
            <div className="item">
              <div className="item-title">
                <span>Gap Signal</span>
                <span className="pill warning">date ambiguity</span>
              </div>
              <div className="item-meta">Critical event sequence needs attorney confirmation.</div>
            </div>

            <div className="item">
              <div className="item-title">
                <span>Contradiction Risk</span>
                <span className="pill danger">statement conflict</span>
              </div>
              <div className="item-meta">Client narration may conflict with existing message timing.</div>
            </div>

            <div className="item">
              <div className="item-title">
                <span>Strategic Opportunity</span>
                <span className="pill good">follow-up question</span>
              </div>
              <div className="item-meta">Probe post-dispute acceptance of performance and related communications.</div>
            </div>
          </div>

          <h3 style={{ marginTop: 8 }}>Candidate Evidence</h3>
          <div className="list">
            {seedEvidence.map((ev) => (
              <div className="item" key={ev.id}>
                <div className="item-title">
                  <span>{ev.id}</span>
                  <span className="pill">{ev.linkState}</span>
                </div>
                <div style={{ marginBottom: 6 }}>{ev.label}</div>
                <div className="item-meta">Type: {ev.type}</div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid grid-2" style={{ marginTop: 16 }}>
        <section className="card">
          <h3>Event / Timeline Sandbox</h3>
          <p>
            This area becomes the intake-side event map. Later it should support drag, merge, dispute,
            and evidence-backed sequencing.
          </p>
          <div className="canvas">
            <div className="empty-state">
              Timeline nodes will appear here as the narrative is decomposed into events. This should
              eventually support what-if scenarios, disputed branches, and attorney-controlled versions
              of the story.
            </div>
          </div>
        </section>

        <section className="card">
          <h3>Attorney Control Layer</h3>
          <p>
            The attorney must be able to control the shape of the intake record and mark what matters.
          </p>
          <div className="list">
            <div className="item">
              <div className="item-title"><span>Lock theory candidate</span><span className="pill">pending</span></div>
              <div className="item-meta">Promote narrative objects into early claim theory structure.</div>
            </div>
            <div className="item">
              <div className="item-title"><span>Flag for deposition</span><span className="pill">future phase</span></div>
              <div className="item-meta">Send high-value intake facts forward into deposition planning.</div>
            </div>
            <div className="item">
              <div className="item-title"><span>Mark client credibility risk</span><span className="pill warning">sensitive</span></div>
              <div className="item-meta">Preserve attorney-only strategic notes around narrative weakness.</div>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
