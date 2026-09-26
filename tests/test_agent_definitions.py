"""Test: an agent definition that cannot be tested is refused.

What should be true (Layer 5): an assistant has one job, its inputs and outputs
are written down, it may not write into the record, every fact it produces
carries a source, weak evidence is staged, and the definition tells you how to
judge the thing like you would judge a person doing the task.

The checker is only worth having if it fails on the definitions that matter. So
each rule below is proved twice: once on a definition that breaks it, and once on
the shipped example, which must pass everything. A checker that is green on
everything is checking nothing.

Run:  python tests/test_agent_definitions.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import agent_check

FAILS = []


def check(label, cond, detail=""):
    ok = bool(cond)
    print(("  PASS  " if ok else "  FAIL  ") + label
          + (("   [" + detail + "]") if detail and not ok else ""))
    if not ok:
        FAILS.append(label)


def results_by_id(text):
    return {r["id"]: r for r in agent_check.check_text(text)}


GOOD = """---
agent: fit-scorer
job: Score one person against the fit definition and say why.
reads:
  - People/
writes:
  - _staging/ready/
  - _staging/weak/
may-not-write:
  - People/
  - _ledger/events.jsonl
proposes-only: true
provenance: required
evidence-floor: two sourced facts from different parts of the record
staging: _staging/weak/
---

## How to judge it, like a person doing the task

- Every fact it cites can be found where it says it came from.
- The verdict follows from the facts it listed, not from an impression.
- It says it does not know often enough to be believable.
"""


def variant(**changes):
    """The good definition with one line altered, so one rule breaks at a time."""
    out = []
    for line in GOOD.splitlines():
        key = line.split(":")[0].strip()
        if key in changes:
            replacement = changes[key]
            if replacement is None:
                continue
            out.append(replacement)
        else:
            out.append(line)
    return "\n".join(out) + "\n"


print("\n=== 1. the shipped example passes every rule ===")

example = ROOT / "agents" / "example-fit-scorer.md"
check("the worked example exists", example.exists(), str(example))
res = {r["id"]: r for r in agent_check.check_file(example)}
bad = [k for k, r in res.items() if not r["ok"]]
check("the worked example passes every rule", not bad,
      "; ".join("%s: %s" % (k, res[k]["detail"]) for k in bad))
check("there are at least ten rules", len(agent_check.RULES) >= 10,
      str(len(agent_check.RULES)))

print("\n=== 2. a control definition passes, so failures below mean something ===")

check("the control passes every rule",
      all(r["ok"] for r in results_by_id(GOOD).values()),
      str([k for k, r in results_by_id(GOOD).items() if not r["ok"]]))

print("\n=== 3. two jobs in one assistant is refused ===")

two_jobs = variant(**{"job": "job: Score the person and then draft the message to send them."})
check("a job joined by 'and then' fails",
      results_by_id(two_jobs)["one-job"]["ok"] is False)

many = variant(**{"job": "job: Score the person. Draft a reply. Update the record."})
check("three sentences of job fails",
      results_by_id(many)["one-job"]["ok"] is False)

print("\n=== 4. an assistant that could write the record is refused ===")

open_record = GOOD.replace("may-not-write:\n  - People/\n  - _ledger/events.jsonl",
                           "may-not-write:\n  - _ledger/events.jsonl")
check("no protection on the people folder fails",
      results_by_id(open_record)["record-is-protected"]["ok"] is False)

contradiction = GOOD.replace("writes:\n  - _staging/ready/",
                             "writes:\n  - People/\n  - _staging/ready/")
check("a folder both allowed and forbidden fails",
      results_by_id(contradiction)["no-contradiction"]["ok"] is False)

print("\n=== 5. unsourced output and unstaged guesses are refused ===")

check("provenance set to anything but required fails",
      results_by_id(variant(**{"provenance": "provenance: nice to have"}))
      ["provenance-required"]["ok"] is False)
check("no evidence floor fails",
      results_by_id(variant(**{"evidence-floor": None}))
      ["evidence-floor-stated"]["ok"] is False)
check("a staging folder outside _staging fails",
      results_by_id(variant(**{"staging": "staging: People/pending/"}))
      ["weak-evidence-staged"]["ok"] is False)
check("an assistant that commits rather than proposes fails",
      results_by_id(variant(**{"proposes-only": "proposes-only: false"}))
      ["proposes-only"]["ok"] is False)

print("\n=== 6. a definition with no way to judge it is refused ===")

no_judging = GOOD.split("## How to judge it")[0]
check("no judging section fails",
      results_by_id(no_judging)["judging-criteria"]["ok"] is False)

thin = GOOD.replace(
    "- The verdict follows from the facts it listed, not from an impression.\n"
    "- It says it does not know often enough to be believable.\n", "")
check("fewer than three criteria fails",
      results_by_id(thin)["judging-criteria"]["ok"] is False)

empty_bullets = GOOD.split("## How to judge it")[0] + \
    "## How to judge it, like a person doing the task\n\n- \n- \n- \n"
check("three blank bullets is not three criteria",
      results_by_id(empty_bullets)["judging-criteria"]["ok"] is False)

print("\n=== 7. the checker reads and never writes ===")

before = example.read_text(encoding="utf-8")
agent_check.check_file(example)
check("checking a definition does not alter it",
      example.read_text(encoding="utf-8") == before)

src = (ROOT / "engine" / "agent_check.py").read_text(encoding="utf-8")
mutations = []
for i, line in enumerate(src.splitlines(), 1):
    s = line.strip()
    if s.startswith("#") or s.startswith('"'):
        continue
    if any(m in s for m in ("os.replace", ".mkdir(", ".unlink(", ".rename(", ".write_text(")):
        mutations.append("%d: %s" % (i, s[:60]))
    if "open(" in s and any(mode in s for mode in ('"w"', "'w'", '"a"', "'a'")):
        mutations.append("%d: %s" % (i, s[:60]))
check("the checker has no way to change what it checks", not mutations,
      "; ".join(mutations[:3]))

print("\n=== 8. every rule states the question it answers ===")

check("each rule carries a plain-English question",
      all(q and len(q.split()) >= 4 for _, q, _ in agent_check.RULES))
check("each result carries a detail a person could act on",
      all(r["detail"] for r in agent_check.check_text(GOOD)))

print("\n%s" % ("ALL PASS" if not FAILS else "FAILURES: " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
