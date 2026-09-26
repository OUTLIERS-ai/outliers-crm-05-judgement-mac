**This is the Mac version.** On Windows, use [outliers-crm-05-judgement](https://github.com/OUTLIERS-ai/outliers-crm-05-judgement).

# Outliers CRM - Layer 5 - Judgement

Your CRM records what happened. It has no opinion about any of it. It cannot tell
you whether a person is worth an hour of your week, whether a reply is warm or
merely polite, or which of forty records deserves reading first.

This layer adds the part that forms a view, and the rules that stop that view
quietly becoming a fact in your records.

## Install it

    python3 install.py

One command. It finds the CRM you built in Layer 1, asks you two questions in
your own words, and installs the layer into it. Nothing leaves your computer,
nothing costs money, and no account is needed.

The two questions are:

- **What makes someone a good fit for you, in your words?**
- **What would make you drop a lead?**

Both halves matter. A definition with only the good half teaches an assistant to
find reasons to say yes, and every record contains something encouraging if you
go looking for it.

## What it needs beneath it

Layer 4. The installer checks, and stops politely if the layer below is not
there. The layers are cumulative: this one reads records that Layer 1 created,
identified the way Layer 2 decided, holding events Layer 3 defined, captured by
the collectors Layer 4 turned on. Skipping down the ladder gives you an assistant
with nothing to form a view about.

## What it installs

| Path in your CRM | What it is |
|---|---|
| `_judgement/fit-definition.md` | Your words about who is worth your time. Yours to edit. Nothing else writes to it. |
| `_agents/fit-scorer.md` | A worked example of an agent definition, filled in and ready to read. |
| `_agents/_template/` | A blank to copy when you add another. |
| `_engine/agent_check.py` | Reads a definition and reports, rule by rule, whether it is usable. |
| `_engine/provenance.py` | Sourcing a fact and staging a weak one, as code rather than as a good intention. |
| `_staging/ready/` | Proposals with enough evidence to be worth your attention. |
| `_staging/weak/` | Proposals without it. Kept, never promoted. |

## What an agent actually is

An assistant given one job, its own written instructions, and permission to use
particular things. That is the whole of the word, which is used far more loosely
elsewhere.

The written instructions are the markdown file in `_agents/`. The permissions are
the two lists at the top of it: what it may read, and what it may write. There is
a third list, and it is the one people forget: what it may **never** write.

## The three rules this layer rests on

**One job each, never one big one.** An assistant doing everything cannot be
tested in parts. When the output is wrong you cannot tell which half is wrong,
and a change that fixes one behaviour breaks another you never touched.

**Every fact says where it came from and when.** An assistant's accurate output
and its invented output are formatted identically: same tone, same confidence,
same shape on the page. The source line is the only thing that separates them a
fortnight later.

**Weak evidence goes to a review pile, not into the record.** Thin evidence is
not worthless and it is not a fact either. It gets written down somewhere marked
uncertain, and it stays visibly uncertain until you look at it.

## How to judge one, like a person doing the task

You already know what good and bad look like when a human does a job for you. Use
exactly that. Read a few outputs the way you would read a new starter's first
afternoon of work:

- Can you find every fact it cited, in the place it said it came from?
- Does the verdict follow from the facts it listed, rather than from an
  impression it could not point to?
- Does it ever say it does not have enough to go on? An assistant that is always
  confident is not judging, it is guessing fluently.

## Check a definition

In Terminal, from your CRM folder (if your CRM is not at `~/CRM`, put your own folder in the `cd` line):

    cd ~/CRM
    python3 _engine/agent_check.py _agents/

It reports rule by rule and changes nothing. The exit code is the number of
failing rules, so you can wire it into anything later.

## Run the tests

From the folder you downloaded:

    cd ~/outliers-crm-05-judgement-mac
    python3 tests/test_agent_definitions.py
    python3 tests/test_provenance_and_staging.py

Both print a line per assertion and exit non-zero on any failure. Standard
library only.

## What this layer leaves for the next one

Several assistants working at once, any of which could end up putting a message
in front of a real human being. Nothing yet controls the order they run in, how
much they collectively do, or what happens when one of them is wrong. Control
that does not depend on them behaving well is Layer 6.

This repo is made automatically from outliers-crm-05-judgement@7cd2e82. To report a problem or suggest a change, use that repo, not this one.
