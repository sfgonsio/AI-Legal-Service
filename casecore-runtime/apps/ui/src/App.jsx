import { useMemo, useState } from "react";

export default function App() {
  const transcript = [
    {
      id: "T1",
      time: "00:11",
      side: "client",
      preview: "Built cannabis businesses together with verbal and operational ownership agreements...",
      text: "I built these cannabis businesses with him, and we had verbal and operational agreements about ownership, profits, and decision-making."
    },
    {
      id: "T2",
      time: "00:24",
      side: "client",
      preview: "Yolo Farms, Direct Source, and Preferred Gardens tied to work, money, branding...",
      text: "Yolo Farms, Direct Source, and Preferred Gardens were all tied to work, money, branding, and opportunities that I helped create and fund."
    },
    {
      id: "T3",
      time: "00:39",
      side: "agent",
      preview: "System identifying ownership, oral partnership, fiduciary-duty, accounting theories...",
      text: "I am identifying possible claims involving ownership, oral partnership, fiduciary duties, accounting, and diversion of assets or opportunities."
    },
    {
      id: "T4",
      time: "00:54",
      side: "client",
      preview: "Money went in, businesses grew, then control and distributions moved away...",
      text: "Money went in, businesses grew, and then control, distributions, and business opportunities started moving away from me."
    },
    {
      id: "T5",
      time: "01:07",
      side: "client",
      preview: "Emails, texts, ownership discussions, financials, licensing materials exist...",
      text: "There are emails, texts, ownership discussions, financials, licensing materials, and records tied to Polley, Tumber, Yolo Farms, Direct Source, and Preferred Gardens."
    },
    {
      id: "T6",
      time: "01:21",
      side: "agent",
      preview: "System marking ownership, partnership duty, diversion, and damages proof needs...",
      text: "I am marking places where proof of ownership, partnership duties, diverted money, and damages may need supporting evidence."
    }
  ];

  const markers = [
    {
      id: "M1",
      left: "10%",
      type: "story",
      title: "Oral partnership / shared build",
      detail: "Jeremey describes building the cannabis businesses together and ties his role to ownership, profit-sharing, and decision-making.",
      impact: "Supports partnership and ownership theories."
    },
    {
      id: "M2",
      left: "28%",
      type: "story",
      title: "Ownership / control rights",
      detail: "Jeremey describes agreed ownership, operational participation, and control expectations involving Yolo Farms, Direct Source, and Preferred Gardens.",
      impact: "Supports ownership, fiduciary-duty, and declaratory-relief theories."
    },
    {
      id: "M3",
      left: "49%",
      type: "story",
      title: "Asset and opportunity diversion",
      detail: "Jeremey describes control, money, distributions, and opportunities moving away from him after the businesses were built.",
      impact: "Supports fiduciary-duty, accounting, and misappropriation theories."
    },
    {
      id: "M4",
      left: "73%",
      type: "story",
      title: "Entity and evidence references",
      detail: "Jeremey identifies emails, texts, financials, ownership discussions, and licensing materials tied to key cannabis entities and actors.",
      impact: "Connects the narrative to documentary proof."
    },
    {
      id: "C1",
      left: "31%",
      type: "clarification",
      title: "Need proof of ownership / percentages",
      detail: "The system needs clearer proof of Jeremey’s ownership position, equity percentages, and whether the parties used language of partnership, shared control, or shared profits.",
      impact: "Maps to COA, burden, and evidence support."
    },
    {
      id: "C2",
      left: "53%",
      type: "clarification",
      title: "Need proof of diverted money / opportunities",
      detail: "The system needs records, messages, or financial entries showing money, distributions, business opportunities, or control being redirected away from Jeremey.",
      impact: "Maps to breach, fiduciary-duty, accounting, and damages support."
    },
    {
      id: "C3",
      left: "86%",
      type: "clarification",
      title: "Need damages / accounting support",
      detail: "The system needs records showing what Jeremey contributed, what he expected to receive, what was withheld, and what financial harm resulted.",
      impact: "Maps to burden and remedy support."
    }
  ];

  const coaCards = [
    {
      title: "Breach of Partnership Agreement / Oral Partnership",
      summary: "Possible claim based on verbal partnership promises, shared build-out, shared ownership expectations, and exclusion from agreed benefits or control.",
      burdens: [
        "Show partnership language or conduct establishing a shared venture",
        "Show Jeremey contributed money, work, decisions, or value",
        "Show agreed sharing of ownership, profits, or control",
        "Show breach through exclusion, non-distribution, or denial of agreed rights"
      ],
      evidence: [
        "Texts or emails using ownership or partnership language",
        "Proof Jeremey funded, built, negotiated, or operated",
        "Ownership percentage discussions and business planning",
        "Distribution records and exclusion communications"
      ]
    },
    {
      title: "Breach of Fiduciary Duty",
      summary: "Possible claim if David or others owed duties as partner, manager, or controlling actor and used control, money, brands, or opportunities unfairly.",
      burdens: [
        "Show a fiduciary relationship existed",
        "Show misuse of duty, loyalty, care, or disclosure obligations",
        "Show diversion of assets, money, control, or opportunities",
        "Show resulting harm or need for equitable relief"
      ],
      evidence: [
        "Entity structure and operating records",
        "Decision-making communications and authority references",
        "Financial transfers, ledgers, and distributions",
        "Records showing exclusion, concealment, or redirection"
      ]
    },
    {
      title: "Accounting / Ownership & Equity Dispute",
      summary: "Possible claim if ownership interests, profits, and distributions are disputed and records are incomplete, withheld, or inconsistent.",
      burdens: [
        "Show ownership interest or equitable stake",
        "Show disputed profits, distributions, or transactions",
        "Show records are incomplete, withheld, or contradictory",
        "Show accounting is needed to determine value and harm"
      ],
      evidence: [
        "Financial statements and ledgers",
        "Loan records and capital contributions",
        "Ownership, licensing, and corporate records",
        "Requests for books, records, and explanations"
      ]
    }
  ];

  const evidenceNeeded = [
    "Proof of Yolo Farms ownership position or percentage",
    "Direct Source ownership / funding documents",
    "Preferred Gardens branding / IP ownership references",
    "Texts and emails using partner / ownership language",
    "Financial records showing redirected money or distributions",
    "Documents showing Jeremey contributions and expected returns",
    "Entity records showing decision-making authority",
    "Accounting records showing what was withheld"
  ];

  const summary =
    "The interview currently points to a cannabis-business ownership and partnership dispute involving Yolo Farms, Direct Source, and Preferred Gardens. The system is identifying possible oral partnership, fiduciary-duty, and accounting or ownership-dispute claims. It is also identifying the need for proof of Jeremey’s ownership position, contributions, decision-making role, diversion of money or opportunities, and resulting damages.";

  const [selectedMarkerId, setSelectedMarkerId] = useState("C1");
  const [selectedTranscriptId, setSelectedTranscriptId] = useState("T1");

  const selectedMarker = useMemo(
    () => markers.find((m) => m.id === selectedMarkerId) ?? markers[0],
    [selectedMarkerId]
  );

  const selectedTranscript = useMemo(
    () => transcript.find((t) => t.id === selectedTranscriptId) ?? transcript[0],
    [selectedTranscriptId]
  );

  return (
    <div className="workspace-shell">
      <div className="workspace-grid">
        <section className="panel transcript-panel">
          <div className="panel-head compact">
            <h2>Transcript</h2>
            <div className="controls">
              <button className="btn start">Start</button>
              <button className="btn pause">Pause</button>
              <button className="btn stop">Stop</button>
            </div>
          </div>

          <div className="transcript-list scroll-y">
            {transcript.map((item) => (
              <button
                key={item.id}
                className={`transcript-row ${item.side} ${selectedTranscriptId === item.id ? "active" : ""}`}
                onClick={() => setSelectedTranscriptId(item.id)}
              >
                <span className="row-time">{item.time}</span>
                <span className="row-preview">{item.preview}</span>
              </button>
            ))}
          </div>

          <div className={`transcript-detail ${selectedTranscript.side}`}>
            <div className="detail-meta">
              <span className="detail-role">{selectedTranscript.side === "client" ? "Client statement" : "AI statement"}</span>
              <span className="detail-time">{selectedTranscript.time}</span>
            </div>
            <div className="detail-fulltext">{selectedTranscript.text}</div>
          </div>
        </section>

        <section className="panel timeline-panel">
          <div className="panel-head compact">
            <h2>Audio Timeline + Tags</h2>
            <div className="mini-key">
              <span className="key-item"><span className="key-dot primary" /> story</span>
              <span className="key-item"><span className="key-dot secondary" /> clarify</span>
            </div>
          </div>

          <div className="waveform">
            <div className="wave-bars">
              {Array.from({ length: 96 }).map((_, i) => (
                <span
                  key={i}
                  className={`bar ${i > 86 ? "pending" : ""}`}
                  style={{ height: `${12 + ((i * 19) % 42)}px` }}
                />
              ))}
            </div>

            {markers.map((marker) => (
              <button
                key={marker.id}
                className={`marker ${marker.type} ${selectedMarkerId === marker.id ? "active" : ""}`}
                style={{ left: marker.left }}
                onClick={() => setSelectedMarkerId(marker.id)}
                title={marker.title}
              >
                <span className="marker-line" />
                <span className={`marker-dot ${marker.type}`}>{marker.id}</span>
              </button>
            ))}
          </div>

          <div className="marker-detail">
            <div className="marker-detail-top">
              <div className={`detail-pill ${selectedMarker.type}`}>
                {selectedMarker.type === "story" ? "Story marker" : "Clarification marker"}
              </div>
              <div className="detail-id">{selectedMarker.id}</div>
            </div>
            <div className="detail-title">{selectedMarker.title}</div>
            <div className="detail-text">{selectedMarker.detail}</div>
            <div className="detail-impact">{selectedMarker.impact}</div>
          </div>
        </section>

        <section className="panel coa-panel">
          <div className="panel-head compact">
            <h2>COA + Burden + Evidence</h2>
          </div>

          <div className="coa-stack scroll-y">
            {coaCards.map((card) => (
              <div key={card.title} className="coa-card">
                <div className="coa-title">{card.title}</div>
                <div className="coa-summary">{card.summary}</div>

                <div className="coa-section">
                  <div className="section-label">What must be shown</div>
                  <div className="mini-list">
                    {card.burdens.map((item) => (
                      <div key={item} className="mini-card burden">{item}</div>
                    ))}
                  </div>
                </div>

                <div className="coa-section">
                  <div className="section-label">Evidence that may support it</div>
                  <div className="mini-list">
                    {card.evidence.map((item) => (
                      <div key={item} className="mini-card evidence">{item}</div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel summary-panel">
          <div className="panel-head compact">
            <h2>Summary</h2>
            <button className="btn audio">Play</button>
          </div>
          <div className="summary-box scroll-y">{summary}</div>
        </section>

        <section className="panel evidence-panel">
          <div className="panel-head compact">
            <h2>Evidence Needed</h2>
          </div>
          <div className="evidence-list scroll-y">
            {evidenceNeeded.map((item) => (
              <div key={item} className="evidence-chip">{item}</div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
