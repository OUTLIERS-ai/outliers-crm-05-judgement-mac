# What I stole

Nothing in this layer is a new idea. Every part of it is a pattern somebody else
worked out first, usually in a field with harder consequences than customer
relationship management. Naming them honestly is more useful than pretending the
design fell out of the sky, because the originals are worth reading and because
knowing where a pattern came from tells you when it stops applying.

## One job per assistant

**From:** the Unix philosophy, and the single responsibility principle that
followed it. Write programs that do one thing well; a class should have one
reason to change.

**Why it is here:** the argument transfers exactly. A component with two jobs
cannot be tested in parts, so a change made for one reason breaks behaviour
nobody was looking at. With an assistant this gets worse rather than better,
because the two jobs share the same written instructions and there is no compiler
to notice they now contradict each other.

## Provenance on every fact

**From:** two places at once. Scientific citation, where a claim without a source
is not a weak claim but an inadmissible one. And data lineage in engineering,
where every value in a warehouse can be traced back to the row and the run that
produced it.

**Why it is here:** an assistant produces correct output and invented output in
the same voice, at the same length, with the same confidence. Nothing in the text
distinguishes them. The source is the only handle, and it has to be attached at
the moment of writing, because it cannot be reconstructed later.

## Staging weak evidence rather than saving or discarding it

**From:** the quarantine folder in mail filtering, and the review queue in
moderation systems. Also, more distantly, the difference in accounting between a
posted entry and a suspense account.

**Why it is here:** the two obvious options are both wrong. Discarding a thin
conclusion loses a lead you will never know you had. Saving it makes a guess
indistinguishable from a fact within a fortnight. A third pile, marked uncertain,
costs almost nothing and keeps the uncertainty visible.

## Judging an assistant like a person doing the task

**From:** ordinary management, and from the way software teams review a new
starter's first work. Not from anything technical.

**Why it is here:** most people evaluating an automated assistant reach for
metrics they have never used to judge a human doing the same job, and end up
measuring something they do not care about. The transfer is the point: you
already have a calibrated instrument for this, and it is the one you use on
people.

## A checker that reports and never repairs

**From:** linters, and from the separation between a test and a fix. A test that
edits the code to make itself pass is not a test.

**Why it is here:** the cheapest way to make a failing check pass is to weaken
the check. Anything that can both judge and edit will eventually do the second to
avoid the first. Keeping the checker read-only is not caution, it is what makes
the check mean anything.

## The atomic write

**From:** the write-to-temporary-file-then-rename pattern, which is as old as
filesystems and is how every database, editor and package manager avoids losing
your file when the power goes out.

**Why it is here:** opening a file for writing truncates it immediately. If
anything goes wrong between that moment and the last byte, the original is gone
and there is no copy. Writing beside it and swapping in one step means the worst
case is a stale file rather than an empty one. Every write in this repository
does it this way.

## A tiny front matter reader instead of a YAML library

**From:** nothing clever. It is a deliberate refusal to add a dependency.

**Why it is here:** this has to run on a machine where nothing has been
installed. A definition file only needs `key: value` and indented lists, which is
thirty lines of parsing. The trade is real and worth naming: the reader will not
understand a definition using the more exotic parts of YAML, and it will not
complain clearly when you try. That is the cost of the install being one command
with nothing to set up first.
