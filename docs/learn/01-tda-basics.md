# 01 · Topology from zero

*Day 1, 60 minutes. You need: distances between vectors, and PCA. Nothing else.*

This document gets you from "a bag of points" to "a persistence diagram", by hand, on six
points. Everything snntopo measures is a persistence diagram or a distance between two of
them, so this is the one piece of maths the rest of the packet stands on.

## 1. The question topology asks

Take a rubber band and a coffee mug. You can stretch, bend and squash either one as much as
you like, but you may not cut or glue. Some properties survive every such deformation: the
rubber band is one piece, and it has one hole. So does the mug (the handle). Topology is the
study of the properties that survive. Length, angle, curvature and size do not survive, and
topology ignores them. Those belong to **geometry**: everything about a shape that changes
when you stretch it.

Keep this split in mind for the whole packet. **Topology** = how many pieces, how many holes.
**Geometry** = how big, how round, how far apart. Document 03 turns on it.

Two counts are all we need:

- A **connected component** is a piece. Two separate blobs have two components.
- A **loop** is a closed path that goes around a hole and can't be shrunk to a point without
  leaving the shape. A ring has one loop. A figure-8 has two. A filled disc has none.

Mathematicians call the count of components `H0` and the count of loops `H1` ("homology in
dimension 0 and 1"). **Homology** is the machinery that counts holes of each dimension;
`H2` would count enclosed cavities, like the inside of a hollow ball. The counts themselves
are the **Betti numbers**: a ring has Betti numbers (1, 1), one component and one loop. A
figure-8 has (1, 2). The repo writes these down for its test shapes in
`snntopo/generators.py:15-22`.

## 2. The problem: data is points, not shapes

A **point cloud** is a finite set of points in some space. Example: 150 points in 10
dimensions. A finite set of points has no loops at all, and it has as many components as it
has points. So "count the holes" is meaningless until we decide how to connect the dots.

The obvious fix: pick a distance `t` and join every pair of points closer than `t`. But then
the answer depends on `t`. Too small and nothing is joined. Too large and everything is
joined to everything and all the holes are filled in.

Persistent homology's answer is: don't pick. Do it for every `t` at once and record how the
counts change. Features that exist over a wide range of `t` are taken seriously. Features
that flicker in and out are treated as noise.

## 3. Connecting the dots: the Vietoris-Rips complex

Fix a scale `t`. Build a shape out of the points like this:

- every point is in;
- an **edge** joins two points if their distance is at most `t`;
- a **filled triangle** spans three points if all three pairwise distances are at most `t`
  (and likewise solid tetrahedra for four points, and so on).

A shape built from points, edges, filled triangles and their higher-dimensional cousins is a
**simplicial complex**. The specific rule above, where a triangle is filled the moment
its three edges exist, is the **Vietoris-Rips complex** (Rips for short). Its appeal is that
it needs nothing but the table of pairwise distances.

You can picture the same thing with balls: put a ball of radius `r` on every point. Two
balls touch when the points are within `2r`. So "edges at distance `t`" is "balls of radius
`t/2`". The software this project uses (ripser) reports scales as distances `t`, so that is
what this packet uses too.

Filled triangles matter because they are what closes a hole. Three points joined by three
edges form a little loop. If the triangle is filled, that loop bounds a solid patch and
doesn't count as a hole.

## 4. Growing the scale: a filtration

Now let `t` grow from 0 upward. The Rips complex only ever gains edges and triangles; it
never loses any. A nested sequence of complexes like this, each containing the last, is a
**filtration**. Watching a filtration is like watching a flood rise over a landscape:
islands merge, lakes form and then drain.

As `t` grows, two kinds of event happen:

- two components merge into one (an edge appears between them): one `H0` feature ends;
- a loop appears (an edge closes a cycle that no triangles fill) or disappears (triangles
  finally fill it): an `H1` feature starts or ends.

## 5. Worked example: six points on a circle

Six points evenly spaced on a circle of radius 1, numbered 0 to 5:

```
            2 ● ─ ─ ─ ● 1
             ╱         ╲
          3 ●           ● 0
             ╲         ╱
            4 ● ─ ─ ─ ● 5
```

There are only three distinct distances between pairs:

| pair type | example | distance |
|---|---|---|
| neighbours | 0-1 | 1 |
| skip one | 0-2 | √3 ≈ 1.732 |
| opposite | 0-3 | 2 |

(Neighbours on a unit circle 60° apart are exactly 1 apart: the triangle they form with the
centre is equilateral.)

Now raise `t` and write down what happens.

**`t` from 0 up to just under 1.** No edges. Six separate points. `H0` count is 6, `H1`
count is 0.

**`t` = 1.** All six neighbour edges appear together, and the complex is the outline of a
hexagon. Two things happen at once:

- The six components become one. That takes five merges (joining six things into one always
  takes five joins), so five `H0` features end here.
- The sixth edge closes the ring. Is the ring filled? A triangle needs three points with all
  pairwise distances at most 1, and any three of these points include a pair at distance √3
  or 2. So there are no triangles, the ring is hollow, and an `H1` feature starts.

`H0` count is 1, `H1` count is 1: Betti numbers (1, 1), a circle.

**`t` from 1 up to just under √3.** Nothing changes. This is the range of scales over which
the data "looks like a circle".

**`t` = √3.** The six skip-one edges appear (0-2, 1-3, 2-4, 3-5, 4-0, 5-1), and with them
eight triangles: six thin "ear" triangles of three consecutive points (0-1-2, 1-2-3, …),
each with sides 1, 1, √3, and two big ones (0-2-4 and 1-3-5), each with sides √3, √3, √3.
Is the hexagon ring filled now? Yes: the ears 0-1-2, 2-3-4 and 4-5-0 cover the rim, and the
big triangle 0-2-4 covers the middle. Together they tile the whole hexagon. The loop bounds
a filled patch, so the `H1` feature ends.

(A curiosity you can skip: at this scale the eight triangles close up into a hollow
octahedron, which has a cavity, so an `H2` feature starts here and ends at `t` = 2 when the
opposite edges arrive. This project computes `H0` and `H1` only, so it never sees it.
`snntopo/contracts.py:118`.)

**`t` = 2.** Every pair is joined; everything is filled. One solid blob, forever.

The whole story as Betti numbers, one row per range of scales:

| scale `t` | pieces (`H0`) | loops (`H1`) | the data looks like |
|---|---|---|---|
| 0 to 1 | 6 | 0 | six unrelated points |
| 1 to 1.732 | 1 | 1 | a ring |
| 1.732 and up | 1 | 0 | a blob |

Notice that there is no single right answer to "what shape are these six points?". There is
an answer per scale, and the middle row is the one a person would give. Persistent homology
keeps all three rows and tells you how wide each one is. The ring row is 0.732 wide, which
is a large fraction of the cloud's total width of 2, and that is the sense in which the
ring is a real feature of this data.

## 6. Birth, death, persistence

Each feature in the story has a scale at which it starts, its **birth**, and a scale at
which it ends, its **death**. Its lifetime, death minus birth, is its **persistence**.

For the hexagon:

| feature | birth | death | persistence |
|---|---|---|---|
| `H0` × 5 (the points that got absorbed) | 0 | 1 | 1 |
| `H0` × 1 (the component that survives) | 0 | never | infinite |
| `H1` × 1 (the ring) | 1 | 1.732 | 0.732 |

There are two standard pictures of this table, and they hold the same information:

- A **barcode** draws each feature as a horizontal bar from its birth to its death.
- A **persistence diagram** plots each feature as a point at (birth, death). Every point
  sits above the diagonal line death = birth, and its height above that line is its
  persistence. Points hugging the diagonal are short-lived.

```
barcode                               diagram (H1)
H0 ├──────────┤                       death
H0 ├──────────┤                        2 │
H0 ├──────────┤                          │     ● (1, 1.73)
H0 ├──────────┤                        1 │   ╱
H0 ├──────────┤                          │ ╱  diagonal
H0 ├──────────────────────────▶          └────────── birth
H1            ├───────┤                  0   1    2
   0          1     1.73    2   t
```

The bar that never ends is an **essential bar**. There is always exactly one in `H0`, since
in the end everything is one piece. It carries no information, and this project drops it
before measuring any distance (`snntopo/topology/stats.py:127-130`).

The word "persistent" is the whole idea. A single choice of `t` gives one snapshot, and you
can't tell a real hole from an accident of that particular `t`. A long bar says the feature
is there across a wide range of scales. A short bar says it existed only briefly, which is
what noise in the data produces: jitter the points and tiny loops appear and vanish near the
diagonal.

## 7. A second shape: the figure-8

Take two of those hexagons and glue them at one shared point, side by side, so the shape is
two rings touching at the origin. That is 11 points, and it is 4 wide instead of 2.

Run the same flood. At `t` = 1 both rings close, so **two** `H1` features are born. (Two
extra edges also appear across the join, between the neighbours of the shared point, but
each forms an equilateral triangle with the shared point, which is filled at once. No third
loop.) At `t` = √3 each ring fills in exactly as before. So:

| feature | birth | death |
|---|---|---|
| `H1` × 2 | 1 | 1.732 |

One ring gives one `H1` bar. A figure-8 gives two. That difference in the diagram is a
difference in topology, and it is the "known answer" this project uses to check itself: its
synthetic test shapes are a circle and a figure-8 made of two unit circles meeting at the
origin (`snntopo/generators.py:62-84`), and one of its calibration checks compares exactly
this pair (`snntopo/floor.py:89-109`). Document 03 covers it.

## 8. Comparing two diagrams

To say "these two shapes have similar persistence", we need a distance between diagrams.
Both standard ones work by matching: pair up the points of diagram A with the points of
diagram B, as cheaply as possible. A point with no good partner may be matched to the
diagonal instead, which amounts to saying "this feature is as good as absent"; that costs
more the further the point is from the diagonal.

- **Bottleneck distance**: the cost of the best matching is its single worst pair. It only
  hears the largest disagreement.
- **Wasserstein distance**: the cost is the combined cost over all pairs (for "order 2",
  the root of the sum of squares). It hears every disagreement, including many small ones.

The project computes both through the gudhi library, uses Wasserstein of order 2 for every
verdict, and found bottleneck too insensitive to be useful
(`snntopo/topology/stats.py:3-4, 127-135`; `snntopo/contracts.py:124-127`; E1).

A hand example with the two toy shapes, after scaling each to width 1 (the reason for the
scaling comes in section 10). The hexagon's ring becomes one point at (0.5, 0.866), with
persistence 0.366. The figure-8's two rings become two points at (0.25, 0.433), persistence
0.183 each. The cheapest matching sends all three points to the diagonal. Moving a point
(b, d) to the diagonal costs (d − b)/2 under bottleneck's rule, so the bottleneck distance
is the largest of those: 0.183. Under Wasserstein-2's rule it costs (d − b)/√2, and the
total is √(0.259² + 0.129² + 0.129²) ≈ 0.32. These are toy numbers on noiseless points, for
intuition only. No experiment in this project produced them.

## 9. Stability: small nudges, small changes

Here is the property that makes diagrams usable on noisy data. **Stability** says: if you
move every point of the cloud by at most ε, then each birth and death moves by at most 2ε,
so the bottleneck distance between the old and new diagram is at most 2ε. This is a theorem;
we state it and check it on the example.

Push point 0 outward from radius 1 to radius 1.1. It moved by 0.1. Its distances change:

| pair | before | after |
|---|---|---|
| 0-1 and 0-5 | 1 | 1.054 |
| 0-2 and 0-4 | 1.732 | 1.819 |
| 0-3 | 2 | 2.1 |

Redo the flood. At `t` = 1 the other five points link up into a chain (four merges). Point
0 joins at `t` = 1.054 (the fifth merge), and its two edges close the ring at that same
moment, so the `H1` feature is born at 1.054 instead of 1. At `t` = 1.732 the edges 1-3,
3-5 and 5-1 arrive, and the ring is tiled by the ears 1-2-3 and 3-4-5, the big triangle
1-3-5, and the triangle 0-1-5 (sides 1.054, 1.054, 1.732). It dies at 1.732, as before.

| feature | before | after |
|---|---|---|
| `H0` deaths | 1, 1, 1, 1, 1 | 1, 1, 1, 1, 1.054 |
| `H1` (birth, death) | (1, 1.732) | (1.054, 1.732) |

The point moved 0.1. The diagram moved 0.054, well inside the promised 0.2. Small noise in,
small change out. Without stability, a diagram computed from noisy recordings would mean
nothing.

Stability cuts both ways, though: it promises the diagram won't change *much*, and it also
means the diagram *does* change a little whenever the points do. Noise never leaves a
diagram untouched. Document 03 is about measuring how much it moves from noise alone.

## 10. What topology ignores, and what a diagram doesn't

Go back to section 1: topology ignores stretching. Betti numbers do. A circle of radius 1
and a circle of radius 5 both have Betti numbers (1, 1).

A persistence diagram is not Betti numbers. It records *when* features are born and die, in
units of distance. So:

- Double the radius of the hexagon and every birth and death doubles. Same topology,
  different diagram.
- Squash the hexagon into an ellipse and the ring is born at one scale and filled at a
  different one. Same topology, different diagram.
- Put the points closer together along the ring (denser sampling) and the ring is born
  earlier. Same topology, different diagram.

**A persistence diagram mixes topology with geometry.** The *number* of long bars is
topological. Their *positions and lengths* are geometric. A distance between two diagrams
is sensitive to both, and can be large between two shapes with identical topology.

The project handles the crudest geometric effect, overall size, by rescaling every cloud
so its two farthest points are exactly 1 apart before computing anything
(`snntopo/topology/pipeline.py:35-39`). That is why section 8 scaled the toys to width 1.
But this removes only size. Look at what it did to the two toys: the figure-8's rings have
persistence 0.183 and the hexagon's has 0.366, even though all three rings are identical
hexagons. The figure-8 is simply twice as wide, so each of its rings is a smaller fraction
of the whole. And in the nudged hexagon, the single displaced point sets the new width
(2.1), which rescales every other bar slightly. Rescaling by the diameter makes one pair of
points responsible for the scale of the whole diagram.

Shape differences that aren't topology (ellipse vs circle, uneven sampling, where the ring
sits relative to the rest of the cloud) all survive the rescaling and all show up in diagram
distances. The project learned this the hard way. It took until experiment E12 to pin down
that two *circles* placed differently in space are reliably told apart by its test, and
that this is correct behaviour, not a bug (`snntopo/topology/stats.py:44-47`). Document 03
covers it.

## 11. What to carry forward

- A point cloud becomes a growing family of complexes (a filtration); features are born and
  die as the scale grows; the record is a persistence diagram.
- `H0` bars are about pieces merging. `H1` bars are about rings forming and filling.
- Long bars are structure. Short bars are usually noise.
- Diagrams are stable: small changes to the points, small changes to the diagram.
- Diagrams carry geometry as well as topology. A big distance between diagrams does not, by
  itself, mean different topology.

What this project does with all this, concretely: Rips persistence on `H0` and `H1`, on a
cloud of 150 points scaled to width 1, up to scale 1, compared by Wasserstein distance. What
those 150 points *are* is the subject of document 02, and it is not what you might guess.

## Sources

Optional, all listed with link checks in `dev/agents/project/learning/reading.md`:

- Ghrist, *Barcodes: the persistent topology of data* (2008). The classic short
  introduction. <https://www.ams.org/bull/2008-45-01/S0273-0979-07-01191-3/>
- Chazal & Michel, *An introduction to Topological Data Analysis* (2017). The best fit for
  an ML reader; has the stability theorem stated properly. <https://arxiv.org/abs/1710.04019>
- Otter et al., *A roadmap for the computation of persistent homology* (2015). How it is
  computed and with which software. <https://arxiv.org/abs/1506.08903>
