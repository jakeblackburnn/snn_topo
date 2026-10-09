# 00 · Start here

A two-day reading course on snntopo: how its experiments work, what they really test, where
the work sits in the literature, and where it could go next. Four hours a day. Read in
order; each document assumes the ones before it.

It assumes you know machine learning well and no topology or neuroscience. Every term is
explained in plain words where it first appears, with one concrete example from this repo.

## Day 1 · The instrument (240 minutes)

| minutes | read | it answers |
|---|---|---|
| 10 | `00-start-here.md` | what is in this packet and how to use it |
| 60 | `01-tda-basics.md` | what is a persistence diagram, worked by hand on six points |
| 50 | `02-pipeline.md` | how does one recording become a diagram, step by step in the code |
| 10 | break | |
| 60 | `03-noise-and-floor.md` | when is a difference between two diagrams real |
| 50 | `04-experiments.md` | what did E1 to E18 each ask, find, and fail to find |

## Day 2 · The subjects, the field, the choice (240 minutes)

| minutes | read | it answers |
|---|---|---|
| 40 | `05-brains-and-snns.md` | what are the recordings and the networks, and why they can't yet be compared |
| 10 | `06-literature.md` | what to read in three papers, and what to skip |
| 40 | paper: Curto 2017 | why topology suits neural data at all |
| 60 | paper: Gardner et al. 2022 | what a strong topological result on a brain looks like |
| 40 | paper: Maheswaranathan et al. 2019 | the model-side version of this project's question |
| 20 | `07-what-it-tests.md` | what has been shown, what hasn't, in plain statements |
| 30 | `08-goals.md` | six directions the project could take, with costs |

Links to the three papers are in `06-literature.md`.

## The glossary

`glossary.md` lists every term alphabetically, with a one-line meaning and the document
that introduces it. Use it when a word from an earlier document has slipped. It is a
reminder, not an explanation: the explanation and the example are in the document named.

## How to read the citations

Claims about this project carry a pointer so you can check them:

- `snntopo/floor.py:89-109` means that file, those lines. Read a few as you go. The code
  is short and its comments are good.
- E12, E18 and so on are entries in `dev/agents/experiments.md`. Every result number in
  this packet is copied from there.
- D28 and so on are entries in `dev/agents/decisions.md`: why something was decided.

## What this packet is not

- **Not a set of decisions.** Document 08 lists options and adopts none. Choosing is yours,
  in a later `/brainstorm`.
- **Not new results.** Nothing was run to write it. It describes the code and results on
  the `main` branch as of 2026-10-09.
- **Not a survey of the field.** Three papers are guided closely; twenty more are listed as
  optional.
- **Not exercises.** There is nothing to run.

Three things in it are flagged as unverified where they appear: what the analysis window
means in seconds (02, section 5), the number of points in Gardner's cloud (06), and the
size of the undownloaded Steinmetz data (08, option B).
