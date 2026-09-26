"""
provenance.py - every fact an assistant writes says where it came from and when,
and anything it is not sure about goes to a review pile instead of into the record.

Two ideas, one file.

PROVENANCE. An assistant's accurate output and its invented output look exactly
the same on the page. Both are well-formed sentences in the same tone. The only
thing that separates them later is whether the fact carries a source. So a fact
here is never a bare string: it is a value, a source, and the date it was seen.

STAGING. Judgement is not certainty. An assistant reaches a conclusion from
whatever evidence was in front of it, and sometimes that evidence is thin. Thin
evidence is not worthless and it is not a fact either, so it goes to a folder
marked uncertain, where it stays visible as uncertain until a person looks at it.

What this file deliberately does NOT do is write into your people folder. There is
no function here that touches a person's record. An assistant proposes; you decide.
That is the whole of Layer 5 in one sentence, and it is enforced by there being no
code for the other thing.

    import provenance
    fact = provenance.fact("Runs a two-person studio", source="their profile")
    provenance.submit(vault, agent="fit-scorer", person="Rowan Ashdown",
                      conclusion="good fit", facts=[fact])

Needs: Python 3.8 or newer. Nothing else.
"""

import json
import os
import re
from datetime import date
from pathlib import Path

# How many sourced facts a proposal needs before it is worth a person's time.
# Below this it is still recorded, just in the weak pile. One fact is an
# impression; two independent ones is the start of a case.
EVIDENCE_FLOOR = 2

READY = "ready"
WEAK = "weak"


def _atomic_write(path, content):
    """Write a file without ever damaging one that already exists.

    Writes to a temporary file first, then swaps it into place in a single step.
    If anything goes wrong halfway through, the original is untouched.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def fact(value, source, seen_on=None):
    """One fact, with the two things that make it checkable later.

    `source` is where it came from in words a person could follow back: "their
    profile", "the message they sent", "the meeting recording". `seen_on` is the
    date it was true; facts go out of date and a dated fact ages honestly.
    """
    value = str(value).strip()
    source = str(source or "").strip()
    if not value:
        raise ValueError("a fact needs a value")
    if not source:
        raise ValueError("a fact without a source is not a fact, it is a claim")
    return {"value": value, "source": source, "seen": seen_on or date.today().isoformat()}


def render(f):
    """One line a person can read: the fact, then where it came from."""
    return "%s  (source: %s, seen %s)" % (f["value"], f["source"], f["seen"])


def is_sourced(f):
    return bool(isinstance(f, dict) and f.get("value") and f.get("source") and f.get("seen"))


def _slug(text):
    text = re.sub(r"[^\w\s-]", "", str(text)).strip().lower()
    return re.sub(r"[\s_-]+", "-", text) or "unknown"


def staging_dir(vault, pile=READY):
    return Path(vault) / "_staging" / pile


def submit(vault, agent, person, conclusion, facts, floor=EVIDENCE_FLOOR):
    """Record one proposal. Returns the path it was written to.

    Every proposal is written down. The only decision made here is WHICH pile:
    enough sourced facts and it goes to the ready pile for review, otherwise it
    goes to the weak pile. Nothing is discarded, because a discarded proposal is
    a lead you will never know you had, and nothing is promoted, because promotion
    is a person's job.

    A fact with no source is refused outright rather than stored unsourced. An
    unsourced fact in a review pile is indistinguishable from an invented one
    the moment you stop remembering the run that produced it.
    """
    facts = list(facts or [])
    for f in facts:
        if not is_sourced(f):
            raise ValueError("every fact must carry a value, a source and a date: %r" % (f,))

    pile = READY if len(facts) >= floor else WEAK
    record = {
        "agent": str(agent),
        "person": str(person),
        "conclusion": str(conclusion),
        "facts": facts,
        "evidence-count": len(facts),
        "evidence-floor": floor,
        "pile": pile,
        "written": date.today().isoformat(),
        "accepted": False,
    }

    folder = staging_dir(vault, pile)
    base = "%s--%s" % (_slug(agent), _slug(person))
    target = folder / (base + ".json")
    n = 2
    while target.exists():
        target = folder / ("%s-%d.json" % (base, n))
        n += 1
    _atomic_write(target, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return target


def staged(vault, pile=None):
    """Everything waiting for a person, newest last. Read only."""
    out = []
    for name in ((pile,) if pile else (READY, WEAK)):
        folder = staging_dir(vault, name)
        if not folder.exists():
            continue
        for f in sorted(folder.glob("*.json")):
            try:
                record = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                continue
            record["file"] = str(f)
            out.append(record)
    return out


def summary(vault):
    """Counts per pile, for a one-line report."""
    rows = staged(vault)
    counts = {READY: 0, WEAK: 0}
    for r in rows:
        counts[r.get("pile", WEAK)] = counts.get(r.get("pile", WEAK), 0) + 1
    return counts


# There is deliberately no accept(), commit() or write_to_record() in this file.
# Moving a proposal into a person's record is a human act, and the absence of the
# function is the guarantee. If it existed, something would eventually call it.
