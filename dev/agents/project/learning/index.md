# Learning packet: a 2-day reading course on snntopo

> Context packet, written 2026-10-09 from `dev/main.md`, `dev/journal.md` (Oct 9) and a
> `/context-builder` interview. It plans a document packet; it is not the document packet.
> Line numbers were checked on `main` @ `94ede27`.

## What and why

Jake built snntopo with agents and doesn't yet understand it well enough to steer it
(`dev/journal.md:5-9`). Before the project is re-framed he wants to learn how the experiments
work, what they actually test, and where the work sits in the literature. The build writes a
numbered set of markdown documents under `docs/learn/` that he reads over two days, 4 hours each,
ending in a list of candidate project goals he can choose from in a later `/brainstorm`.

The reader: strong in ML (backprop, PCA, RNNs, permutation tests, effect sizes need no
explanation). New to topology and to neuroscience: homology, persistence, spike recordings,
brain regions and trial structure are explained from zero.

## Scope

**In:** ten markdown files (nine numbered documents and a glossary) under `docs/learn/`
(`documents.md` lists them), written from the repo and from the papers in `reading.md`.

**Out:**
- Any reframe decision: new goals, new experiments, code changes, edits to `dev/main.md`.
  The last document lists options; it adopts none.
- Running anything: no `python`, `pytest`, `snntopo`. No runnable exercises (dropped in the
  interview, since the builder can't verify their output).
- The parked grid task (`grid-measure`, `e88be9e`): described in one section as an open
  problem, not continued.
- Notebooks, HTML, images. Diagrams are ASCII so the docs read in nvim.

## Where things live

| need | file |
|---|---|
| what/why, scope, done-when, roadmap, build process, choices, open questions | this file |
| the schedule, the documents and what each must contain, the repo source map | `documents.md` |
| the reading list with checked links, and the findings the docs depend on | `reading.md` |

## Done when

- [x] `ls docs/learn/` shows exactly: `00-start-here.md`, `01-tda-basics.md`, `02-pipeline.md`,
      `03-noise-and-floor.md`, `04-experiments.md`, `05-brains-and-snns.md`, `06-literature.md`,
      `07-what-it-tests.md`, `08-goals.md`, `glossary.md`.
- [x] `wc -w docs/learn/0*.md` is within each document's word budget in `documents.md` (±15%).
- [x] `00-start-here.md` holds the two-day schedule in timed blocks; the blocks of each day sum
      to 240 minutes.
- [x] Every term in `glossary.md` is defined in plain words in the document that first uses it,
      and each of documents 01-05 contains one worked example taken from this repo (a named
      session, run dir, generator or E-number).
- [x] Every claim about this project carries a `path:line`, a D-number or an E-number.
      `grep -c 'E[0-9]\|D[0-9]\|\.py:' docs/learn/0[2-5]*.md` is nonzero for each file, and a
      spot check of 10 citations resolves on `main`.
- [x] Every number about a result is quoted from `dev/agents/experiments.md` with its E-number.
      None is computed, rounded differently, or recalled.
- [x] Every URL in `docs/learn/` appears in `reading.md` or was opened by the builder and added
      to it with the date: `grep -oh 'https\?://[^) >]*' docs/learn/*.md | sort -u` against
      `reading.md`.
- [x] `06-literature.md` gives, for each of the three core papers, what to read, what to skip
      and three questions to answer while reading, written from the paper's own text.
- [x] `08-goals.md` lists 4-6 candidate goals, each with the question it answers, what exists
      toward it, the cost and a done-when. It contains no recommendation and no ranking.
- [x] `git diff --stat main learn-docs` touches only `docs/learn/` and the builder's own
      `dev/agents/` files. `git status` on `grid-measure` is unchanged by the build.

## Roadmap

One commit per milestone on `learn-docs`. Each check is a read-only command.

| # | milestone | check |
|---|---|---|
| M0 ✓ | `learn-docs` branched from `main`; `glossary.md` started with the terms listed in `documents.md` | `git branch --show-current` |
| M1 ✓ | `01-tda-basics.md`, `02-pipeline.md` | word counts; the worked 6-point example is complete by hand; every pipeline step cites `path:line` |
| M2 ✓ | `03-noise-and-floor.md`, `04-experiments.md` | every E1-E18 entry appears once in 04 with its recorded verdict; numbers match `experiments.md` |
| M3 ✓ | `05-brains-and-snns.md`, `07-what-it-tests.md` | 07 has no claim that 02-05 don't support (each line points back to a section) |
| M4 ✓ | `06-literature.md` | the three papers were opened this session; guidance quotes real section or figure names |
| M5 ✓ | `08-goals.md` | 4-6 options, no recommendation; each option cites its source in the repo or in `reading.md` |
| M6 ✓ | `00-start-here.md`, glossary complete, link and citation pass | every done-when box above |

## Build process

**Who:** one agent, sequentially. The documents share a glossary and build on each other, so
there is nothing to parallelize.

**Sandbox (interview, 2026-10-09):**
- Writes: `docs/learn/` only, plus the builder's own `dev/agents/` journal.
- Commands: none that execute project code. No `python`, `pytest` or `snntopo`. Reading the
  repo is fine (`ls`, `grep`, `wc`, `sed -n`, `git log/show/diff`). Web fetch is allowed, to
  open the papers in `reading.md`.
- Git: branch `learn-docs` from `main`, commit there. No merge, no push, no branch deletion.
  `grid-measure` is not touched.
- Project rules in `CLAUDE.md` still apply. Never edit `dev/main.md`, `dev/journal.md`, or any
  run dir.

**Gap policy:** assume and note. Pick the reasonable reading, record the assumption in the
builder's journal, keep going.

**Must not:**
- State a number it didn't copy from `experiments.md` or a run's recorded verdict.
- Describe a paper it couldn't open. If the full text is unreachable, say so in the document
  and guide from the abstract only.
- Repeat a claim from the poster report or the 09-23 brainstorm without checking it against
  D28-D38 and `dev/brainstorm/snn-tda-dataset/seed-errata.md` (`reading.md`, "Stale sources").
- Recommend a goal, or describe the grid subsample as part of the pipeline.

**Style:** Jake's explain rules. Plain words first; each term defined the first time it
appears; one concrete example per idea; no proofs. Second person is fine. Short paragraphs,
ASCII diagrams, tables only for things that are tables.

## Choices made

| choice | why |
|---|---|
| Reframe is decided after the learning | goals picked before understanding the instrument would repeat the E1-E11 pattern |
| This project first, literature second | the papers land better once he knows what a point cloud is here |
| 4 h/day, 8 h total | his answer; the schedule has no optional padding inside the 8 h |
| Intuition plus one hand-worked computation, no proofs | his answer |
| Three guided core papers: Curto 2017, Gardner 2022, Maheswaranathan 2019 | why topology for neural codes; the field's reference result and the nearest method; the model-side version of this project's question |
| No exercises | the builder can't run code, so it couldn't verify them |
| Markdown in `docs/learn/` | reads in nvim, versioned with the code |
| Docs describe `main` | the grid work on `grid-measure` has never been run |
| Goals document lists options with costs, no recommendation | the choice is his, in a later `/brainstorm` |

## Open questions

None blocking.

1. "No runs" is read here as "no project code"; `git`, `grep` and `wc` are assumed allowed,
   since committing and the done-when checks need them.
2. The `WINDOW` comment may be wrong (`reading.md`, finding 3). The builder reports what the
   code does and flags the comment; it doesn't settle it.
