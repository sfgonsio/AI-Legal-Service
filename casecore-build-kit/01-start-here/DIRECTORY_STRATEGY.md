\# /casecore-spec/docs/governance/DIRECTORY\_STRATEGY.md



\# DIRECTORY STRATEGY



\## Purpose



This document defines the two distinct directory models used by CASECORE:



1\. Authoritative system-of-record specification directory

2\. Builder-facing execution/build directory



These are related but not identical.



\---



\## 1. Authoritative Directory



Root:

`/casecore-spec`



Purpose:

\- long-term maintenance

\- source of truth

\- governance

\- auditability of the specification itself

\- change control

\- storage of canonical specifications



This directory is authoritative.



All specification updates must land here first.



\---



\## 2. Builder-Facing Directory



Root:

To be created later as a derived build kit.



Purpose:

\- engineering handoff

\- faster implementation navigation

\- build sequencing

\- developer onboarding

\- execution-oriented grouping



This directory is derived from the authoritative directory and must never become an independent source of truth.



\---



\## Rules



1\. `/casecore-spec` is the authoritative source

2\. Builder-facing materials must be derived from `/casecore-spec`

3\. No conflicting duplicate definitions may exist across directories

4\. Cleanup and normalization occur in `/casecore-spec` first

5\. Internal system naming must use `casecore`

