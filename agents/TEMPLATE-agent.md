---
agent: name-it-after-the-job
job: One sentence saying the single thing this assistant does.
reads:
  - People/
  - (anything else it needs, one per line)
writes:
  - _staging/ready/
  - _staging/weak/
may-not-write:
  - People/
  - _ledger/events.jsonl
  - _schema/expectations.json
proposes-only: true
provenance: required
evidence-floor: say how much evidence is enough, in your own words
staging: _staging/weak/
---

# Name it after the job

Copy this file, fill it in, then run the checker over it, from your CRM folder:

    python3 _engine/agent_check.py _agents/your-file.md

(on Windows: `python _engine/agent_check.py _agents/your-file.md`)

The checker will tell you which parts are missing. It never changes the file.

## The one job

Say it again in a short paragraph. If you find yourself writing "and also", stop
and make a second assistant instead.

## What it reads

List the places it is allowed to look. Nothing else.

## What it may write

List the places it is allowed to write. These should all be staging folders. An
assistant proposes; you decide.

## What it may never write

List the places it must never touch. The people folder belongs here. So does the
event log, and so does anything that defines the standard the assistant is judged
against.

## Provenance

Say what a fact from this assistant has to carry. The default, and the one worth
keeping: the fact, where it came from, and the date it was seen.

## Staging

Say what counts as enough evidence, and say plainly that anything below that goes
to the weak pile rather than into the record.

## How to judge it, like a person doing the task

At least three things a person could check by reading one output. Observable,
not admirable. "Every fact it cites can be found where it says it came from" is
checkable. "Uses good judgement" is not.

- 
- 
- 
