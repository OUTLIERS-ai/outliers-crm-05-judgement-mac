"""
Outliers CRM - Layer 5 - Judgement

Adds judgement to the CRM you already have. Up to now the system records what
happened. It cannot tell you whether a person is worth an hour of your week, or
whether a reply is warm or merely polite. This layer installs the parts that let
an assistant form a view, and the rules that keep its views out of your records
until you have looked at them.

    python install.py

It finds the CRM you built in Layer 1, asks you two questions in your own words,
and installs the layer into it.

Nothing here costs money and nothing leaves your computer. No account, no
sign-up, no internet connection required.

Needs: Python 3.8 or newer. Nothing else.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

# The command a member types to start Python: `python3` on a Mac, which has no plain
# `python` command, and `python` everywhere else, as the Windows guides print it.
PY = "python3" if sys.platform == "darwin" else "python"

# The key a member presses. A Mac keyboard's key is Return; Windows keeps Enter, exactly as before
# (Mac build plan V3, wave s1: the Session 7 ruling on the words installers print).
KEY = "Return" if sys.platform == "darwin" else "Enter"

LAYER = 5
LAYER_NAME = "Judgement"
NEEDS_LAYER = 4

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- small helpers

# No colour codes anywhere. Plenty of terminals print them as literal gibberish
# and a member's first minute with this must not look broken. Plain text works
# everywhere, which is the whole point of the exercise.
BOLD = DIM = OFF = ""


def say(msg=""):
    print(msg, flush=True)


def ask(question, default=None, helptext=None):
    """One plain question. Enter accepts the default."""
    say()
    say(BOLD + question + OFF)
    if helptext:
        say(DIM + "  " + helptext + OFF)
    prompt = "  > " if default is None else "  [%s] > " % default
    try:
        answer = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        say("\nStopped. Nothing was changed.")
        sys.exit(1)
    return answer or (default or "")


def ask_yes(question, default=True):
    d = "Y/n" if default else "y/N"
    a = ask(question, default=d).strip().lower()
    if a in ("y/n", "y/n".upper(), "y", "yes"):
        return True if a != "y/n" else default
    if a in ("n", "no"):
        return False
    return default


def write(path, content):
    """Write a file without ever damaging one that already exists.

    Writes to a temporary file first, then swaps it into place in a single step.
    If anything goes wrong halfway through, the original is untouched. This is a
    habit worth keeping: the notes in here are the record, and there is no copy.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def copy_in(src, dst):
    """Copy one file into the CRM, using the same safe write as everything else."""
    write(dst, Path(src).read_text(encoding="utf-8"))


def keep_cache_out_of_history(home):
    """Python leaves compiled cache folders beside any code it runs.

    They are noise, they change constantly, and they do not belong in the history
    of your records. Adding two lines to the ignore file costs nothing and saves a
    confusing first look at what changed.
    """
    path = Path(home) / ".gitignore"
    try:
        current = path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        return
    if "__pycache__" in current:
        return
    head = (current.rstrip() + "\n\n") if current.strip() else ""
    write(path, head
          + "# Python leaves these beside any code it runs. Not part of your CRM.\n"
          + "__pycache__/\n"
          + "*.pyc\n")


# -------------------------------------------------------------- finding the CRM

def config_path(home):
    return Path(home) / "_layers" / "config.json"


def looks_like_a_crm(home):
    try:
        return config_path(home).exists()
    except OSError:
        return False


def find_vault():
    """Find the CRM Layer 1 built, by looking for its config file.

    Layer 1 writes _layers/config.json into the folder it builds. That file is
    how every later layer knows where the CRM is, what you call the people in it,
    and how far up the ladder you have got.
    """
    tried = []
    env = os.environ.get("OUTLIERS_CRM")
    if env:
        tried.append(Path(env).expanduser())
    # Layer 1 leaves a pointer naming wherever the member chose to put their CRM.
    # Without checking it, anyone who declined the default folder is told they have
    # not done Layer 1 when they have, which reads as the series being broken.
    pointer = Path.home() / ".outliers-crm"
    if pointer.exists():
        try:
            noted = pointer.read_text(encoding="utf-8").strip()
            if noted:
                tried.append(Path(noted))
        except OSError:
            pass
    tried.append(Path.home() / "CRM")
    here = Path.cwd()
    tried.append(here)
    tried.extend(here.parents)

    for candidate in tried:
        if looks_like_a_crm(candidate):
            return Path(candidate)

    say()
    say("  Could not find your CRM automatically.")
    raw = ask("Where is it?",
              default=str(Path.home() / "CRM"),
              helptext="The folder Layer 1 built. It has a _layers folder inside it.")
    candidate = Path(raw.strip().strip('"').strip("'")).expanduser()
    return candidate if looks_like_a_crm(candidate) else None


def load_config(home):
    try:
        return json.loads(config_path(home).read_text(encoding="utf-8"))
    except Exception:
        return {}


def refuse_politely(reason):
    say()
    say("=" * 66)
    say("  Not yet.")
    say("=" * 66)
    say()
    say("  " + reason)
    say()
    return 1


# ------------------------------------------------------------------ the interview

def interview(cfg):
    people_word = cfg.get("people_word", "contacts")
    say()
    say("=" * 66)
    say("  OUTLIERS CRM   LAYER %d   %s" % (LAYER, LAYER_NAME.upper()))
    say("=" * 66)
    say()
    say("  Your CRM records what happened. It has no opinion about any of it.")
    say("  This layer adds assistants that form a view, and the rules that stop")
    say("  their views quietly becoming facts in your records.")
    say()
    say(DIM + "  Two questions, in your own words. Press %s to accept a default." % KEY + OFF)

    fit = ask("What makes someone a good fit for you, in your words?",
              default="",
              helptext="Plain sentences. What you would say if a friend asked who "
                       "you want to work with. Skip it and you get a blank to fill in.")

    drop = ask("What would make you drop a lead?",
               default="",
               helptext="The things that end it. Wrong size, wrong problem, "
                        "cannot decide, cannot pay, gone quiet.")

    return {
        "fit": fit.strip(),
        "drop": drop.strip(),
        "people_word": people_word,
    }


# ------------------------------------------------------------------ what we build

def fit_definition(answers, cfg):
    fit = answers["fit"] or (
        "(Write it here. Plain sentences, your own words. The assistant reads this\n"
        "file and nothing else about what a good fit means, so vagueness here comes\n"
        "back to you as vague verdicts.)")
    drop = answers["drop"] or (
        "(Write it here. What ends it. This half matters more than the first: an\n"
        "assistant with no reason to say no will say yes to everyone.)")
    return """---
date: {today}
type: fit-definition
owner: you
---

# What a good fit looks like, in my words

This file is yours. Assistants read it. Nothing writes to it except you.

It is deliberately prose, not a scoring formula. You are not trying to build a
model. You are writing down what you already know, so that something else can
apply it consistently while you are doing something more useful.

## A good fit

{fit}

## What would make me drop it

{drop}

## Why both halves are here

A definition with only the good half teaches an assistant to find reasons to say
yes. Every record contains something encouraging if you go looking. The reasons
to stop are what make the verdict mean anything, and they are the half most
people never write down.

## Keeping it honest

When you overrule one of the assistant's verdicts, come back here and ask why.
Usually the answer is that you knew something this file does not say. Add it.
The definition getting better is the point; the assistant is only ever as good as
this page.
""".format(today=date.today().isoformat(), fit=fit, drop=drop)


def personalise_agent(text, answers, cfg):
    """Point the shipped example at this member's own fit definition."""
    people_word = answers.get("people_word", "contacts")
    return text.replace("the owner's written definition of a good fit",
                        "your written definition of a good fit") \
               .replace("the owner wrote in their own words",
                        "you wrote in your own words") \
               .replace("the owner's words about what makes someone worth\ntheir time",
                        "your words about what makes someone worth your time") \
               .replace("the owner's own vocabulary", "your own vocabulary") \
               .replace("The owner", "You") \
               .replace("one person's record", "one %s record" % people_word.rstrip("s"))


def readme(answers, cfg):
    w = cfg.get("people_word", "contacts")
    return """# Judgement

**What is in here**

| Path | What it holds |
|---|---|
| `_judgement/fit-definition.md` | Your words about who is worth your time. Yours to edit; nothing else writes to it. |
| `_agents/` | One file per assistant. Each says what its single job is and what it may touch. |
| `_agents/_template/` | A blank to copy when you add one. |
| `_staging/ready/` | Proposals with enough evidence to be worth your attention. |
| `_staging/weak/` | Proposals without it. Kept, not promoted. |
| `_engine/agent_check.py` | Reads an assistant's definition and says whether it is usable. |
| `_engine/provenance.py` | The rules for sourcing a fact and staging a weak one, as code. |

**What an assistant is**

An assistant given one job, its own written instructions, and permission to use
particular things. That is the whole of the word. The instructions are the file
in `_agents/`; the permissions are the two lists at the top of it.

**Check a definition**

    {py} _engine/agent_check.py _agents/

It reports rule by rule and changes nothing.

**The three rules this layer rests on**

1. One job each. An assistant doing two things cannot be tested in parts, and
   fixing one behaviour breaks another you never touched.
2. Every fact carries its source and its date. An accurate output and an invented
   one are formatted identically; the source is the only thing that separates
   them a fortnight later.
3. Weak evidence is staged, never saved. What is uncertain stays visibly
   uncertain until you look at it.

**Judging one**

Like a person doing the task. You already know what good and bad look like when
somebody does this job for you. Read a few outputs the way you would read a new
starter's first afternoon of work: are the facts real, do they point where the
verdict points, and does it ever admit it does not know.

**Your {w}**

Nothing in this layer edits them. There is no code here that writes into your
people folder, which is a stronger guarantee than a rule saying it must not.
""".format(w=w, py=PY)


def layer_note(answers, cfg):
    return """# Layer {n} - {name}

**What it built.** A place to write down who is worth your time, in your own
words. A format for defining an assistant: one job, what it reads, what it may
write, what it must never write. A checker that reads a definition and says
whether it is usable. Two staging folders, one for proposals with evidence behind
them and one for proposals without.

**What it does.** It lets something other than you form a view about a person,
without that view becoming a fact in your records. Assistants propose. You decide.
The separation is enforced by there being no code in this layer that writes into
your people folder.

**The idea worth keeping.** You already know how to judge whether a person did a
job well. Judge an assistant exactly the same way: read a few of its outputs,
check that the facts are real, check that the verdict follows from them, and
check that it sometimes says it does not know. An assistant that is never
uncertain is not judging, it is guessing fluently.

**What it leaves for Layer {nxt}.** Several assistants can now be working at
once, and any one of them could end up putting a message in front of a real human
being. Nothing yet controls the order they run in, how much they collectively do,
or what happens when one of them is wrong. Control that does not depend on them
behaving well is the next layer.
""".format(n=LAYER, name=LAYER_NAME, nxt=LAYER + 1)


# ------------------------------------------------------------------------- build

def build(home, answers, cfg):
    say()
    say("Installing Layer %d into %s" % (LAYER, home))
    say()

    def note(path, what):
        say("  built  %-40s %s" % (str(Path(path).relative_to(home)), what))

    p = home / "_judgement" / "fit-definition.md"
    if p.exists():
        say("  kept   %-40s %s" % ("_judgement/fit-definition.md",
                                   "already there, and it is yours; left alone"))
    else:
        write(p, fit_definition(answers, cfg))
        note(p, "your words about who is worth your time")

    p = home / "_agents" / "fit-scorer.md"
    write(p, personalise_agent(
        (HERE / "agents" / "example-fit-scorer.md").read_text(encoding="utf-8"),
        answers, cfg))
    note(p, "a worked example: one job, written down")

    p = home / "_agents" / "_template" / "agent-definition-template.md"
    copy_in(HERE / "agents" / "TEMPLATE-agent.md", p)
    note(p, "a blank to copy when you add one")

    for name in ("agent_check.py", "provenance.py"):
        p = home / "_engine" / name
        copy_in(HERE / "engine" / name, p)
        note(p, "the checker" if name == "agent_check.py" else "sourcing and staging, as code")

    for pile in ("ready", "weak"):
        d = home / "_staging" / pile
        d.mkdir(parents=True, exist_ok=True)
        keep = d / "README.md"
        if not keep.exists():
            write(keep, "# The %s pile\n\n%s\n" % (
                pile,
                "Proposals with enough sourced evidence to be worth reading."
                if pile == "ready" else
                "Proposals without enough evidence. Kept so nothing is lost, and not\n"
                "promoted, because promoting a guess is how a guess becomes a fact\n"
                "nobody can trace back."))
        say("  built  %-40s %s" % ("_staging/%s/" % pile,
                                   "proposals with evidence behind them"
                                   if pile == "ready" else
                                   "proposals without it, kept and not promoted"))

    p = home / "_judgement" / "README.md"
    write(p, readme(answers, cfg))
    note(p, "what this layer is and how to use it")

    p = home / "_layers" / ("Layer %d - %s.md" % (LAYER, LAYER_NAME))
    write(p, layer_note(answers, cfg))
    note(p, "what this layer did, for when you forget")

    keep_cache_out_of_history(home)

    cfg["layer"] = max(int(cfg.get("layer", 0) or 0), LAYER)
    cfg["fit-definition"] = "_judgement/fit-definition.md"
    cfg["evidence-floor"] = 2
    cfg["layer-%d-installed" % LAYER] = date.today().isoformat()
    write(config_path(home), json.dumps(cfg, indent=2) + "\n")


def finish(home, answers, cfg):
    say()
    say("=" * 66)
    say("  Done. Your CRM can now hold an opinion.")
    say("=" * 66)
    say()
    say("  Check the example assistant's definition. From inside %s:" % home)
    say()
    say("      %s _engine/agent_check.py _agents/" % PY)
    say()
    say("  It reads the definition and reports rule by rule. It changes nothing.")
    say()
    say("  What to do now:")
    say("    1. Open _judgement/fit-definition.md and finish it in your own words.")
    say("    2. Let the assistant score a few real records against it.")
    say("    3. Overrule one, then read the reason it gave. That is the whole")
    say("       layer: you find out whether it was thinking or guessing, and you")
    say("       find out what your own definition left out.")
    say()
    say("  Nothing in here writes to your people folder. Proposals land in")
    say("  _staging, and they stay there until you move them.")
    say()


def main():
    home = find_vault()
    if not home:
        return refuse_politely(
            "Layer %d needs Layer 1 first. Run that one and come back." % LAYER)

    cfg = load_config(home)
    have = int(cfg.get("layer", 0) or 0)
    if have < NEEDS_LAYER:
        return refuse_politely(
            "Layer %d needs Layer %d first. Run that one and come back.\n\n"
            "  Your CRM at %s is on Layer %d."
            % (LAYER, NEEDS_LAYER, home, have))

    answers = interview(cfg)
    say()
    say("  Installing into:   %s" % home)
    say("  Good fit:          %s" % (answers["fit"] or "(left blank, fill it in after)"))
    say("  Drop it when:      %s" % (answers["drop"] or "(left blank, fill it in after)"))
    if not ask_yes("Go ahead?", default=True):
        say("\nStopped. Nothing was changed.")
        return 1
    build(home, answers, cfg)
    finish(home, answers, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
