# Discovery Interviews: FA Industry-Research Workflow

## Status and evidence boundary

**Status: awaiting interviews.** This document contains the approved, privacy-preserving interview protocol and a synthesis structure; it does not contain participant findings. No participant sessions have been supplied or conducted in the project record. Consequently, no time ranges, pain-point rankings, product changes, or go/no-go result are claimed below.

This is deliberately a pre-build evidence record. It must be completed from 2–3 real conversations with boutique-FA interns or junior analysts whose industry-research task was completed within the previous 90 days. Do not begin product-code work on the basis of this template alone.

### Privacy rules

- Assign a sequential session code (`DV-01`, `DV-02`, then `DV-03` if needed).
- Do not record a person’s name, employer, client, deal, project, contact detail, confidential document, or verbatim sensitive information.
- Capture role level only as `intern` or `junior analyst`; record research-work recency as a rounded range.
- Record time only as participant-reported ranges, never as measured facts unless a later user test measures it.
- Store paraphrased workflow evidence and non-sensitive examples only.

## Session protocol

Use the questions below in the same order for every participant. First reconstruct the participant’s existing workflow. Do not describe or pitch the proposed product until question 9.

1. Think of the most recent industry-research task you completed in the last 90 days. What was its purpose and deadline? Please omit confidential context.
2. Starting from receipt of the task, what did you do next? Walk through each step in order and name the tools used.
3. For each step, what was your participant-reported time range? Include scoping, searching, extraction or note taking, reconciling conflicting information, citation cleanup, and writing.
4. Which actions involved repeating searches, copying information between tools, or reformatting material? What made them repetitive?
5. Describe any source or citation failure you encountered: inaccessible material, an unsupported conclusion, mismatched source content, an out-of-date source, or conflicting figures. How did you discover and resolve it?
6. Who reviewed the work, if anyone? What corrections were requested and how were they made?
7. What confidentiality or process constraints shaped the way you researched, stored evidence, or shared a draft?
8. Which part of the workflow was most difficult or risky? Why?
9. Now consider a workflow that moves from a confirmed research framework, to traceable evidence, to a brief generated only from reviewed evidence. What part would help, and what concerns would you have?
10. Would you accept an evidence-review checkpoint before a brief is generated? Why or why not?
11. What single condition would stop you from using such a workflow?

### Per-session capture template

Use one instance of this template per completed session. Paraphrase answers; do not add direct identifiers.

| Field | Record |
|---|---|
| Session code | `DV-__` |
| Role level | `intern` or `junior analyst` |
| Research-work recency | Participant-reported rounded range, within 90 days |
| Task type and deadline context | Non-confidential paraphrase |
| Workflow steps and tools | Non-confidential paraphrase |
| Participant-reported time range by step | Scoping / search / extraction / reconciliation / citation cleanup / writing |
| Repeated or copied work | Paraphrase |
| Source or citation failure and correction | Paraphrase |
| Review and correction process | Paraphrase |
| Confidentiality constraints | Paraphrase only |
| Evidence-review checkpoint acceptance | Yes / no / conditional, with paraphrased reason |
| Stop-use condition | Paraphrase |

## Participant register

No eligible sessions have been recorded.

| Session code | Role level | Recency of research work | Non-identifying note |
|---|---|---|---|
| — | — | — | Awaiting an eligible interview |

## Synthesis baseline

The following fields must be filled only after at least two eligible sessions are captured. Values must retain the `participant-reported` label and show the raw contributing session count.

### Current-state workflow and time ranges

| Workflow step | Median participant-reported time range | Contributing sessions | Evidence status |
|---|---|---:|---|
| Scoping | Not yet available | 0 | Awaiting interviews |
| Search | Not yet available | 0 | Awaiting interviews |
| Extraction | Not yet available | 0 | Awaiting interviews |
| Reconciliation | Not yet available | 0 | Awaiting interviews |
| Citation cleanup | Not yet available | 0 | Awaiting interviews |
| Writing | Not yet available | 0 | Awaiting interviews |

For each step, preserve each participant’s reported range in the session record. Report a median range only when the range calculation and the contributing codes are documented without revealing identity.

### Pain-point ranking

Rank only pain points stated in participant sessions. For each item, calculate `frequency × severity`, where frequency is the number of participants reporting the issue and severity uses a documented 1–5 participant-reported impact rating. Report the raw count as `n/N`; do not infer a ranking from the product design.

| Rank | Pain point | Frequency | Severity basis | Frequency × severity | Evidence status |
|---:|---|---:|---|---:|---|
| — | Not yet available | 0 | No participant evidence | — | Awaiting interviews |

### Scope hypotheses to test

| Hypothesis | Evidence supporting | Evidence contradicting | Status |
|---|---|---|---|
| Boutique-FA interns and junior analysts are the appropriate first user | Not yet available | Not yet available | Untested |
| An embodied-intelligence pilot is an appropriate first research domain | Not yet available | Not yet available | Untested |
| An evidence-first workflow with an explicit review checkpoint fits current practice | Not yet available | Not yet available | Untested |

### Design implications and product changes

No interview-derived product changes have been made. The signed-off scope remains a design hypothesis, not validated evidence, until the completed interview synthesis supports or changes it.

## Comparable baseline task for Task 10

Use the same baseline task in the later user test, without coaching during task completion:

> 为一次内部项目讨论，形成中国具身智能商业化进展的证据底稿，并对照全球技术趋势。

For the current-state baseline, ask participants to reconstruct how they would complete this task using their normal process and record their participant-reported time ranges by the six workflow steps above. For the Task 10 product test, use the same task statement and record observed completion time, manual interventions, accepted/edited/discarded evidence, export, and the exact repeat-use answer. Compare the two only for the same participant and label the baseline as participant-reported versus the product-test time as observed. Do not claim the ≥30% task-time-improvement target until both measures exist for the relevant participants.

## Go/no-go decision record

**Decision: not assessed; no-go for proceeding unchanged under the validation gate.**

The required evidence does not yet exist. The gate permits proceeding unchanged only when at least two participants both:

1. report material repetitive search, extraction, or citation work; and
2. accept an evidence-review checkpoint.

If the completed interviews do not meet both conditions, revise the target workflow in the signed-off design specification and implementation plan before product code is written. If they do meet the conditions, update this document with raw session counts, the evidence summary, and the resulting decision before code begins.
