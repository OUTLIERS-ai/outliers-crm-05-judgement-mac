"""Test: a fact without a source is refused, and a weak conclusion is staged.

What should be true (Layer 5): an assistant's output is only usable if you can
follow every fact in it back to where it came from, and a conclusion it is not
sure about must not end up sitting in the record looking exactly like one it was
sure about.

Why it needs a test rather than a rule in a document: an assistant told to source
its facts will sometimes not, and the failure is invisible because the unsourced
output reads better than the sourced one. So the code refuses instead.

Run:  python tests/test_provenance_and_staging.py
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import provenance

FAILS = []


def check(label, cond, detail=""):
    ok = bool(cond)
    print(("  PASS  " if ok else "  FAIL  ") + label
          + (("   [" + detail + "]") if detail and not ok else ""))
    if not ok:
        FAILS.append(label)


VAULT = Path(tempfile.mkdtemp(prefix="crm-layer5-test-"))

print("\n=== 1. a fact carries its source and its date ===")

f = provenance.fact("Runs a two-person studio", source="their profile", seen_on="2026-04-11")
check("the value survives", f["value"] == "Runs a two-person studio")
check("the source survives", f["source"] == "their profile")
check("the date survives", f["seen"] == "2026-04-11")
check("a fact reads as one line with its source",
      "source: their profile" in provenance.render(f), provenance.render(f))

undated = provenance.fact("Asked about pricing", source="their message")
check("a fact with no date given still gets one", bool(undated["seen"]))

print("\n=== 2. a fact with no source is refused, not stored unsourced ===")

refused = False
try:
    provenance.fact("Definitely ready to buy", source="")
except ValueError:
    refused = True
check("an unsourced fact raises rather than saving", refused)

refused_empty = False
try:
    provenance.fact("", source="their profile")
except ValueError:
    refused_empty = True
check("an empty fact raises too", refused_empty)

print("\n=== 3. enough evidence goes to the ready pile ===")

path = provenance.submit(
    VAULT, agent="fit-scorer", person="Rowan Ashdown",
    conclusion="likely fit",
    facts=[provenance.fact("Runs a two-person studio", "their profile"),
           provenance.fact("Asked what a retainer costs", "their message")])
record = json.loads(Path(path).read_text(encoding="utf-8"))
check("it lands in the ready pile", record["pile"] == "ready", record["pile"])
check("the evidence count is recorded", record["evidence-count"] == 2)
check("it is not marked accepted", record["accepted"] is False)
check("the conclusion is kept with the facts", record["conclusion"] == "likely fit")
check("every stored fact still carries a source",
      all(provenance.is_sourced(x) for x in record["facts"]))

print("\n=== 4. thin evidence is kept, and kept apart ===")

weak_path = provenance.submit(
    VAULT, agent="fit-scorer", person="Mara Quennell",
    conclusion="might be a fit",
    facts=[provenance.fact("Job title mentions operations", "their profile")])
weak = json.loads(Path(weak_path).read_text(encoding="utf-8"))
check("one fact is below the floor", weak["pile"] == "weak", weak["pile"])
check("it is written down rather than discarded", Path(weak_path).exists())
check("the weak pile is a different folder from the ready pile",
      Path(weak_path).parent != Path(path).parent)

counts = provenance.summary(VAULT)
check("the summary counts both piles", counts == {"ready": 1, "weak": 1}, str(counts))

print("\n=== 5. two proposals about the same person do not overwrite each other ===")

second = provenance.submit(
    VAULT, agent="fit-scorer", person="Rowan Ashdown",
    conclusion="still a likely fit",
    facts=[provenance.fact("Hired their first employee", "their profile"),
           provenance.fact("Booked a call", "the calendar")])
check("the second proposal gets its own file", Path(second) != Path(path))
check("the first is still there and unchanged",
      json.loads(Path(path).read_text(encoding="utf-8"))["conclusion"] == "likely fit")
check("both are visible to a reviewer",
      len([r for r in provenance.staged(VAULT, "ready")]) == 2)

print("\n=== 6. an unsourced fact cannot be smuggled into a proposal ===")

smuggled = False
try:
    provenance.submit(VAULT, agent="fit-scorer", person="Tobias Fenwick",
                      conclusion="great fit",
                      facts=[{"value": "Seems keen", "source": "", "seen": "2026-04-11"}])
except ValueError:
    smuggled = True
check("a proposal carrying an unsourced fact is refused whole", smuggled)
check("and nothing was written for that person",
      not any("tobias" in r["file"].lower() for r in provenance.staged(VAULT)))

print("\n=== 7. nothing in this layer can write into the record ===")

src = (ROOT / "engine" / "provenance.py").read_text(encoding="utf-8")
offenders = []
for i, line in enumerate(src.splitlines(), 1):
    s = line.strip()
    if s.startswith("#"):
        continue
    if "People" in s and any(w in s for w in ("open(", "write", "replace", "mkdir")):
        offenders.append("%d: %s" % (i, s[:60]))
check("no code path here touches the people folder", not offenders,
      "; ".join(offenders[:3]))
check("there is no accept or commit function",
      not any(hasattr(provenance, n) for n in ("accept", "commit", "write_to_record")),
      "an assistant proposes; a person decides, and the missing function is the guarantee")

print("\n=== 8. a half-written file can never replace a good one ===")

target = VAULT / "_staging" / "ready" / "atomic-probe.json"
provenance._atomic_write(target, '{"first": true}\n')
provenance._atomic_write(target, '{"second": true}\n')
check("a rewrite leaves valid content, never a truncated file",
      json.loads(target.read_text(encoding="utf-8")) == {"second": True})
check("no temporary file is left behind",
      not list(target.parent.glob("*.tmp")),
      str(list(target.parent.glob("*.tmp"))))

shutil.rmtree(VAULT, ignore_errors=True)

print("\n%s" % ("ALL PASS" if not FAILS else "FAILURES: " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
