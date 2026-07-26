# Graphics — The Progression of Brain Complexity

Visualizations of brain "complexity" across 19 animals, treated as a
**multi-dimensional quality function** rather than a single score. The central
argument — consistent with the [comparative synthesis](../animals/00-comparative-synthesis.md) —
is that **which animal "leads" depends entirely on which dimension you weight.
There is no single ladder.**

## What's here

| File | What it is |
|------|-----------|
| [`brain-complexity.html`](brain-complexity.html) | Self-contained **interactive** page — biological brain complexity across 19 animals (hover tooltips, cognition-axis toggle, weighting presets, light/dark). |
| [`brain-vs-ai.html`](brain-vs-ai.html) | Self-contained **interactive** page — **LLMs vs biological brains** on the honest parameters↔synapses axis (see [doc 19](../animals/19-artificial-minds-llms.md)). |
| `png/` | Static PNG of each chart (`*.png` for the biological set, `ai-*.png` for the LLM set), plus full-page exports |
| `svg/` | Static SVG (vector) of each chart |
| `data/brain-complexity.csv` | The underlying biological dataset (source of truth) |

## The LLM comparison (`brain-vs-ai.html`)

A companion page placing large language models beside biological nervous systems on
the **one defensible shared axis: learned connections** — synapses in a brain,
parameters in a model (never parameters↔neurons). The finding: frontier LLMs sit at
**mouse-scale** connection counts (~10¹²), ~100–1000× below the human ~10¹⁴–10¹⁵
synapses, reaching language via a completely different bargain (10⁴–10⁵× more
training data, vastly more energy). Charts: the connections lollipop, the scaling
trajectory vs biological reference lines, data-efficiency, energy, and a
transcends-vs-diverges summary. Full analysis in
[doc 19, *Artificial Minds — LLMs in the Comparison*](../animals/19-artificial-minds-llms.md).

## The six charts

1. **Every animal as a profile** — parallel coordinates across all dimensions; crossing lines = rankings disagree.
2. **The two best cognition predictors** — associative-forebrain neurons vs encephalization quotient.
3. **Neurons vs brain size** — log–log scaling with separate mammal/bird trend lines (why a raven rivals a monkey).
4. **The ranking reshuffles** — the same 11 vertebrates ranked five different ways (the core point).
5. **One composite index** — a single weighted score whose ranking rearranges as you change the weights.
6. **Complexity in deep time** — when each neural innovation first appeared.

## Dimensions (the quality functions)

Brain mass · total neurons · associative-forebrain neurons (cortex/pallium;
central-brain estimate for invertebrates) · encephalization quotient (EQ) ·
neuron density · cognition score.

## Assumptions & caveats

- **Complexity is modeled as a vector**, and the charts deliberately show that the
  ranking depends on the chosen weighting — not a linear progression.
- **Numbers are best-estimates** from the neuroscience literature (chiefly
  Herculano-Houzel neuron counts) with real uncertainty; one species stands in for
  a group. The softest values (notably cetacean counts and avian EQ) are flagged in
  the interactive tooltips.
- **The cognition score (0–10) is subjective** — assigned from documented capacities
  (tool use, self-recognition, planning, social learning, communication), *not* a
  measurement. It can be toggled off in the interactive version to see rankings on
  hard numbers only.
- **Invertebrate counts are not strictly comparable** to vertebrates (≈⅔ of octopus
  neurons are in its arms; "associative neurons" has no exact invertebrate
  equivalent).
- Counts/mass/density use **log scales** (the data spans 302 neurons to ~257
  billion). Educational, **not a definitive ranking**.

## Regenerating the static exports

The PNG/SVG files are rendered from `brain-complexity.html` via a headless
Chromium (Playwright) screenshot pass; the HTML is the single source of truth for
the charts, and `data/brain-complexity.csv` for the numbers.

Palette follows the repo's data-viz standards (colorblind-safe: the three main
clades use the validated blue/orange/aqua trio, the small basal-vertebrate group a
neutral gray, and clade identity is carried redundantly by marker shape).
