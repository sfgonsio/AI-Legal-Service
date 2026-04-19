# Project Overview

This is a legal platform that enables and empowers attorneys to provide legal services. 
The platform is an end-to-end tool that is workflow based.
The platform consists of: 
* Spine (connects ai-agents, internal/external information sources), 
* Brain (learns, evolves, applies reason, ability to apply context, prediction, automation)
* AI_Agent (performs specific tasks and accessess resources to complete tasks
* Program (python programs that suppor the Spine, Brain, and AI_Agents and connect capabilities and features to the DB
* Data - Cononical (Authoritative legal grounded)data stream and non-canonical data streams to that support building the case and all eleements
Workflow and orchestration of PHASES:
1. INTAKE:
  * Client articulates case, AI_Agent/Brain ingests and applies legal authoritative rules (CA Evidence Code, CA Jury Instruction, other)
  * AI_Agent asks questions to build a preliminary COA (cause of action), burdens, and remedies
  * AI Agent summarizes the case and validates the firm has understanding from client, packages for attorney to accept, reject, ask for more
  * With attorney acceptance, agreement a contract is the trigger for AI_Agent to support client in upload of Evidence
  * AI_Agent supports client in identifying 'actors' and labeling; plaintiff, defendants, potetnial deponents and roles
  * DB instance built for case and COA, complaint, burden, remedies, are hashed and loaded
2. COA:
  * Complaint is finalized, Case hardens with COA, Burdens, Remedies
3. MAPPING:
  * All evidence is mapped and tagged to complaints, COA, burdens, and remedies fully ID for traceability
  * strengths and weaknesses and how well the case supports the case with Evidence and Fact building
4. DISCOVERY:
  * Pleasdings and Interrogatories created based on strengthening case, weakening opposition to Evidence and Facts
  * Strategy and execution planning
  * intake Interrogatories are mapped, tagged and hashed into DB
  * "War-Room" for Deposition planning that includes what-if analysis
  * Strategy and deposition plan with questions
  * intake the video from deposition, marking and tagging to COA, burden, remedies, evidence, and Facts
5. TRIAL SETTLEMENT:
  * prepare for Trial or Settlement
6. CLOSE CASE
  * TBD
  
