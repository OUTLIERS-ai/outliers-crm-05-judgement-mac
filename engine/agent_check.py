"""
agent_check.py - reads an agent definition and says whether it obeys the rules.

An "agent definition" is a plain markdown file describing one assistant: the single
job it does, what it is allowed to read, what it is allowed to write, what it must
never write, and how you would judge whether it did the job well. Layer 5 of your
CRM is built on the idea that an assistant with one written job can be tested, and
an assistant with a vague job cannot.

This script is the test. It reads a definition file and reports, rule by rule,
whether the definition is usable. It never changes the file. It never runs the
agent. It only reads what you wrote down and tells you what is missing.

    python _engine/agent_check.py _agents/fit-scorer.md
    python _engine/agent_check.py _agents/            (checks every .md in the folder)
    python _engine/agent_check.py _agents/ --json

The exit code is the number of failing rules, so another script can act on it.

Needs: Python 3.8 or newer. Nothing else.
"""

import json
import re
import sys
from pathlib import Path

# The command a member types to start Python: `python3` on a Mac, which has no plain
# `python` command, and `python` everywhere else, as the Windows guides print it.
PY = "python3" if sys.platform == "darwin" else "python"


def _typed(name):
    """The program `name` (it sits beside this file) as the member types it from the folder
    they are in: `_engine/<name>` from the CRM folder, `<name>` from inside `_engine`."""
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    try:
        typed = os.path.relpath(path)
    except ValueError:                      # the member is on another drive
        typed = path
    if typed.startswith(".."):
        typed = path
    typed = typed.replace("\\", "/")
    return '"%s"' % typed if " " in typed else typed


def _agents_typed(rest=""):
    """A path in the CRM's `_agents` folder as the member types it from the folder they are in:
    `_agents/<rest>` from the CRM folder, `../_agents/<rest>` from inside `_engine`. The whole
    path is built first and then quoted if it has a space, so a shell reads it as 1 argument."""
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_agents")
    try:
        typed = os.path.relpath(path)
    except ValueError:                      # the member is on another drive
        typed = path
    typed = typed.replace("\\", "/") + "/" + rest
    return '"%s"' % typed if " " in typed else typed

# The keys a definition must carry in its front matter (the block between the two
# lines of three dashes at the top of the file).
REQUIRED_KEYS = ("agent", "job", "reads", "writes", "may-not-write",
                 "proposes-only", "provenance", "evidence-floor", "staging")

JUDGING_HEADING = "how to judge it"


# ----------------------------------------------------------------- the parser

def parse_front_matter(text):
    """Read the key/value block at the top of a definition.

    Deliberately small. It understands `key: value` and a key followed by
    indented `- item` lines, which is all a definition needs. Using a tiny reader
    rather than a library keeps this file dependency-free, which matters because
    the check has to run on a machine where nothing has been installed.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    block = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        block.append(line)

    meta = {}
    key = None
    for line in block:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and key is not None:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(stripped[2:].strip())
            continue
        if ":" in line and not line[:1].isspace():
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip()
            meta[key] = v if v else []
    return meta


def parse_sections(text):
    """Return {heading in lower case: body text} for every `##` heading."""
    out = {}
    current = None
    buf = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                out[current] = "\n".join(buf)
            current = line[3:].strip().lower()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        out[current] = "\n".join(buf)
    return out


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    value = str(value).strip()
    return [value] if value else []


# ------------------------------------------------------------------ the rules
#
# Each rule answers one question in plain English and returns (passed, detail).
# The detail is written so that a person reading a failure knows what to change,
# not just that something is wrong.

def rule_has_every_key(meta, sections, text):
    missing = [k for k in REQUIRED_KEYS if k not in meta or not as_list(meta.get(k))]
    return (not missing,
            "missing: " + ", ".join(missing) if missing
            else "all %d required keys present" % len(REQUIRED_KEYS))


def rule_one_job(meta, sections, text):
    """One job, said in one sentence.

    An assistant given two jobs cannot be tested in parts. When it goes wrong you
    cannot tell which half went wrong, and fixing one half breaks the other. The
    cheapest guard against that is refusing to write down two jobs in one line.
    """
    job = " ".join(as_list(meta.get("job")))
    if not job:
        return False, "no job is stated"
    sentences = [s for s in re.split(r"[.!?]+", job) if s.strip()]
    if len(sentences) > 1:
        return False, "the job runs to %d sentences; one job is one sentence" % len(sentences)
    joins = [j for j in (" and then ", " also ", "; ", " as well as ")
             if j in job.lower()]
    if joins:
        return False, ("the job joins two jobs with '%s'; split it into two agents"
                       % joins[0].strip())
    words = len(job.split())
    if words > 30:
        return False, "the job is %d words; if it needs that many it is more than one job" % words
    return True, "one job, %d words" % words


def rule_inputs_named(meta, sections, text):
    reads = as_list(meta.get("reads"))
    return bool(reads), ("%d input(s) named" % len(reads)) if reads else "nothing is named as an input"


def rule_outputs_named(meta, sections, text):
    writes = as_list(meta.get("writes"))
    return bool(writes), ("%d output(s) named" % len(writes)) if writes else "nothing is named as an output"


def rule_refusals_named(meta, sections, text):
    """What it may NOT write has to be written down too.

    A list of permissions with no list of prohibitions reads as "anything not
    mentioned is probably fine", which is exactly the assumption that lets an
    assistant edit the record it was only supposed to read.
    """
    never = as_list(meta.get("may-not-write"))
    return bool(never), ("%d prohibition(s) named" % len(never)) if never else "nothing is named as forbidden"


def rule_no_contradiction(meta, sections, text):
    writes = [w.rstrip("/").lower() for w in as_list(meta.get("writes"))]
    never = [n.rstrip("/").lower() for n in as_list(meta.get("may-not-write"))]
    clash = sorted(set(writes) & set(never))
    return (not clash,
            "the same target is both allowed and forbidden: " + ", ".join(clash) if clash
            else "permissions and prohibitions do not overlap")


def rule_never_writes_the_record(meta, sections, text):
    """The people folder is off limits.

    An assistant proposes; a person decides. If an assistant can write straight
    into the record then its guesses and its facts end up stored identically, and
    a fortnight later nothing tells them apart.
    """
    never = [n.lower() for n in as_list(meta.get("may-not-write"))]
    guarded = any(n.startswith("people") for n in never)
    return guarded, ("the people folder is listed as forbidden" if guarded
                     else "the people folder is not listed under may-not-write")


def rule_proposes_only(meta, sections, text):
    value = " ".join(as_list(meta.get("proposes-only"))).strip().lower()
    return value in ("true", "yes"), "proposes-only: %s" % (value or "(not set)")


def rule_provenance_required(meta, sections, text):
    """Every fact it writes says where it came from and when.

    An assistant's accurate output and its invented output are formatted
    identically. The source is the only thing that tells them apart later.
    """
    value = " ".join(as_list(meta.get("provenance"))).strip().lower()
    return value == "required", "provenance: %s" % (value or "(not set)")


def rule_evidence_floor(meta, sections, text):
    floor = " ".join(as_list(meta.get("evidence-floor"))).strip()
    return bool(floor), ("the floor is: %s" % floor) if floor else "no evidence floor is stated"


def rule_staging_target(meta, sections, text):
    """Weak evidence goes to a review pile, not into the record.

    Anything below the evidence floor still gets written down, because throwing it
    away loses a lead. It just gets written somewhere marked uncertain, where it
    stays visible as uncertain until a person looks at it.
    """
    staging = " ".join(as_list(meta.get("staging"))).strip()
    if not staging:
        return False, "no staging folder is named"
    if not staging.lower().lstrip("./").startswith("_staging"):
        return False, "the staging folder is '%s'; it must sit under _staging/" % staging
    writes = [w.lower().lstrip("./") for w in as_list(meta.get("writes"))]
    if not any(w.startswith("_staging") for w in writes):
        return False, "the staging folder is named but is not in the list of allowed writes"
    return True, "weak evidence goes to %s" % staging


def rule_judging_criteria(meta, sections, text):
    """You can only trust an assistant you know how to judge.

    You already know what good and bad look like when a person does this job. The
    definition has to say so, in observable terms, or nobody can tell whether the
    thing is working.
    """
    body = None
    for heading, content in sections.items():
        if JUDGING_HEADING in heading:
            body = content
            break
    if body is None:
        return False, "no section whose heading contains '%s'" % JUDGING_HEADING
    bullets = [l.strip().lstrip("-*").strip() for l in body.splitlines()
               if l.strip().startswith(("-", "*"))]
    bullets = [b for b in bullets if b]
    if len(bullets) < 3:
        return False, "only %d criteria written out; three is the floor" % len(bullets)
    return True, "%d criteria a person could check by reading one record" % len(bullets)


RULES = [
    ("every-key-present",      "the definition carries every required key", rule_has_every_key),
    ("one-job",                "one job, stated in one sentence",          rule_one_job),
    ("inputs-named",           "what it reads is written down",            rule_inputs_named),
    ("outputs-named",          "what it writes is written down",           rule_outputs_named),
    ("refusals-named",         "what it may never write is written down",  rule_refusals_named),
    ("no-contradiction",       "nothing is both allowed and forbidden",    rule_no_contradiction),
    ("record-is-protected",    "it may not write into the people folder",  rule_never_writes_the_record),
    ("proposes-only",          "it proposes and never commits",            rule_proposes_only),
    ("provenance-required",    "every fact it writes carries its source",  rule_provenance_required),
    ("evidence-floor-stated",  "the evidence floor is stated",             rule_evidence_floor),
    ("weak-evidence-staged",   "weak evidence goes to a review pile",      rule_staging_target),
    ("judging-criteria",       "you are told how to judge it",             rule_judging_criteria),
]


# ------------------------------------------------------------------- checking

def check_text(text):
    """Run every rule over one definition. Returns a list of result dicts."""
    meta = parse_front_matter(text)
    sections = parse_sections(text)
    out = []
    for rid, question, fn in RULES:
        try:
            ok, detail = fn(meta, sections, text)
        except Exception as err:                       # a broken rule fails loudly
            ok, detail = False, "the rule could not run: %s" % err
        out.append({"id": rid, "question": question, "ok": bool(ok), "detail": detail})
    return out


def check_file(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    return check_text(text)


def targets(argument):
    p = Path(argument)
    if p.is_dir():
        return sorted(p.glob("*.md"))
    return [p]


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    as_json = "--json" in argv
    if not args:
        usage = __doc__.replace("    python _engine/agent_check.py", "    python " + _typed("agent_check.py"))
        usage = re.sub(r"(?<= )_agents/(\S*)", lambda m: _agents_typed(m.group(1)), usage)
        print(usage.replace("    python ", "    %s " % PY))
        return 2

    files = []
    for a in args:
        files.extend(targets(a))
    files = [f for f in files if f.exists()]
    if not files:
        print("No definition files found. Point this at a .md file or a folder of them.")
        return 2

    report = []
    failing = 0
    for f in files:
        results = check_file(f)
        bad = [r for r in results if not r["ok"]]
        failing += len(bad)
        report.append({"file": str(f), "failing": len(bad), "results": results})

    if as_json:
        print(json.dumps({"failing": failing, "files": report}, indent=2))
        return failing

    for entry in report:
        print("")
        print(Path(entry["file"]).name)
        print("-" * max(20, len(Path(entry["file"]).name)))
        for r in entry["results"]:
            mark = "ok  " if r["ok"] else "FAIL"
            print("  %s  %-24s %s" % (mark, r["id"], r["detail"]))
    print("")
    print("%d rule(s) failing across %d definition(s)." % (failing, len(report)))
    if failing:
        print("")
        print("Nothing has been changed. Each failure above is something to write into")
        print("the definition. A definition that cannot pass these rules describes an")
        print("assistant nobody can test.")
    return failing


if __name__ == "__main__":
    sys.exit(main(sys.argv))
