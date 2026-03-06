
Layer 3 — Composite Candidate Engine (This is the key)

Algorithmically:

Cluster facts by:

Similar product name / SKU

Date proximity (± configurable window)

Same seller

Same quantity

Same dollar amount

Communication chain linkage (reply-to, thread ID)

Score cluster cohesion:

for corroboration across distinct sources

for financial match

for timeline consistency

– for contradictions

– for missing key fields

If score > threshold:
→ Propose Composite Event

Output:

Event_Candidate_342:
Type: Sale
Seller: Preferred Gardens
Product: Lavender SKU 222
Date: 06/01/23
Supporting Facts: A, B, C, D
Confidence: 0.87
Conflicts: None

Fully cited.

No invention.

This Is NOT GPT Magic

This is:

Graph clustering

Time-window grouping

Similarity scoring

Rule-weighted inference

GPT may assist in:

Interpreting messy product names

Resolving alias references

Suggesting normalization labels

But the composite formation must be rule-driven + evidence-bound.

Why This Scales to 600,000 Files

Because:

The heavy lift is:

Distributed parsing

Fact indexing

Graph building

Clustering operates over structured facts, not raw files.

600,000 files may become:

3 million chunks

500,000 candidate facts

40,000 composite event candidates

That is graph math, not attorney reading.

The Critical Safeguards

To prevent hallucination and false synthesis:

Composite event must list supporting fact IDs

Each fact must list evidence spans

Every cluster must show confidence + reasoning features used

Attorney can:

Approve

Reject

Merge

Split

No composite becomes authoritative without approval

The system proposes.
Attorney disposes.

This Is the Real Value Proposition

Without this layer:
You built a very sophisticated document search system.

With this layer:
You built a litigation synthesis engine.

That is materially different.

The Hard Follow-Up Question

Do you want composite clustering to be:

A) Fully automatic with attorney review after-the-fact
or
B) Semi-automatic, where attorney sets clustering parameters first

At 600k files, A is probably necessary.

But governance implications differ.

Your call.

lets bang on this a little more.  Mills picks up a check from Ravi on 6/1/23.  Mills deposits $2100 on 6/2/23.  Ravi works at Yolo Farms (interview). Yolo Farms is a subsidiary of Preferred Gardens (interview). can the application piece a story from this and give to attorney.

A) response: Ideally, Fully automatic.  this is where I am looking to the interview agent to det the granularity of the story to support the application managing the composite clustering.

This feels like significant divergence - how much technical rework is being introduced?

Yes — the application can piece that story together and hand it to the attorney as a proposed composite — but only if we enforce one key discipline:

Interview assertions are hypotheses until corroborated by evidence.
They can drive clustering and prioritization, but they cannot be treated as “proven facts” unless mapped to evidence.

With that in place, your example is exactly the kind of thing the system should propose.

Can the system piece together your example?
Inputs you gave

Evidence fact: Mills picks up a check from Ravi on 6/1/23 (source might be email/SMS/photo/check image)

Evidence fact: Mills deposits $2,100 on 6/2/23 (bank record)

Interview assertions (validated narrative):

Ravi works at Yolo Farms

Yolo Farms is a subsidiary of Preferred Gardens

What the system should produce (proposed composite)

Composite Event Candidate: “Check → Deposit transaction”

Event type: Payment / Deposit / Transaction

Date window: 06/01/2023–06/02/2023

Parties: Mills (recipient/depositor), Ravi (payer/check source) (role of Ravi may be “alleged” until evidence confirms payer identity)

Amount: $2,100

Supporting evidence citations:

Doc/Chunk showing “picked up check from Ravi 6/1/23”

Bank deposit record showing $2,100 on 6/2/23

Contextual linkage (from interview narrative, marked as narrative-sourced):

Ravi → Yolo Farms (Narrative assertion)

Yolo Farms → Preferred Gardens (Narrative assertion)

Attorney-facing story (strictly labeled):

“Evidence shows a $2,100 check pickup followed by a $2,100 deposit next day. Narrative asserts payer ‘Ravi’ is associated with Yolo Farms and that Yolo Farms is tied to Preferred Gardens. This suggests a transaction potentially connected to Preferred Gardens operations, but employer/subsidiary links require corroboration.”

That’s the right output: it’s useful, coherent, and honest about certainty.

How does “Fully automatic” work without hallucination?

You’re right to look to the Interview Agent for granularity. Here’s how it should be used:

Interview Agent output becomes “Candidate Context Graph”

From validated narrative it produces:

entities (Mills, Ravi, Yolo Farms, Preferred Gardens)

relationship assertions (works_at, subsidiary_of)

time anchors (approx dates)

event seeds (check pickup)

These are not evidence-backed yet — they are:

NarrativeFact objects (client-asserted)

used as priors to guide extraction and clustering

Evidence ingestion produces “Evidence Fact Graph”

bank deposit events

check mentions / images

email/SMS threads

Composite Engine bridges them with rules + scoring

It creates clusters using:

date proximity (6/1 and 6/2)

amount match ($2,100)

entity overlap (Mills)

narrative proximity (Ravi mentioned near check pickup)

relationship proximity (Ravi ↔ Yolo Farms ↔ Preferred Gardens)

Then it outputs:

EventCandidate with confidence score

explicit “evidence-supported” vs “narrative-only” fields

That’s how you get automatic synthesis without pretending the narrative is proof.

Does this represent significant divergence / technical rework?

Some, but it’s not a rewrite. It’s an explicitization of what we were already circling around.

What is NOT rework

Interview agent stays

Ingestion pipeline stays

Chunk storage stays

Tagging stays

Mapping stays conceptually

What IS new (and should be treated as a new capability)

You are adding a formal layer:

“Composite Event Engine” + supporting data objects

If you don’t already have these, you’ll need to add:

Fact objects (normalized)

NarrativeFact objects (validated interview assertions)

EventCandidate objects (composites)

Scoring + features used for clustering (why it matched)

Evidence citations at the span level for every atomic fact

This is not “refactoring everything,” but it is a material scope addition: a graph-based synthesis subsystem.

Why it feels like divergence

Because earlier we were describing “Mapping Agent connects story to evidence.”
Now we’re specifying how that happens at 600k-file scale:

Not just one-to-one mapping

But many-to-many clustering into composite events

That’s the difference between “linking” and “synthesizing.”

The clean way to avoid spaghetti

Do not bury this inside Mapping Agent as magical behavior.

Instead define a new internal program capability:

COMPOSITE_ENGINE (Program)

Input: Facts + NarrativeFacts + Tags + basic edges

Output: EventCandidates + supporting links + scores

Deterministic: yes (given same inputs + same weights)

LLM optional: only for normalization helpers (product name cleanup, alias suggestion), never for event creation

Mapping Agent then becomes:

a supervisor/curator of fact normalization and edge quality

and a consumer/validator of composite suggestions

This keeps your architecture modular and auditable.

Answer to your “how much rework” question in one line

It’s not a rewrite, but it is a new first-class subsystem (facts/events/composites) that we should formalize now, because it’s central to the 600k-file value proposition.

Proposed Stage 9 decision to lock

If you agree, we lock these as authoritative:

Interview produces NarrativeFacts (hypotheses)

Evidence ingestion produces EvidenceFacts (grounded)

Composite engine generates EventCandidates from both

Every composite explicitly separates:

evidence-grounded support

narrative-only context

Attorneys approve composites to promote them to authoritative Events

If we lock this, everything else (COA, prompts, discovery) becomes reliable.

If you want, next I’ll write the contract-style spec for:

NarrativeFact schema

EvidenceFact schema

EventCandidate schema

Composite scoring features + acceptance tests (including your 6/1 check + 6/2 deposit scenario)