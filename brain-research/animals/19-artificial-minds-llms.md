# Artificial Minds — LLMs in the Comparison

> **This is not an animal.** It is the artificial counterpart to the comparative
> menagerie — included to ask a specific question: when you place large language
> models beside biological nervous systems on the *same honest axes*, is there a
> pattern that transcends the biological/artificial divide? The answer is a
> qualified yes for **scaling and distributed computation**, and an emphatic no for
> **efficiency and learning** — and the interesting part is exactly where the line
> falls. This document is a companion to [doc 14, *Neural Computation & the Brain–AI
> Comparison*](../docs/14-neural-computation-and-ai.md), which covers the mechanistic
> side; here the focus is the quantitative comparison.

## Table of Contents
- [The unit problem: what maps to what](#the-unit-problem-what-maps-to-what)
- [Scale: where LLMs actually sit](#scale-where-llms-actually-sit)
- [Patterns that transcend the divide](#patterns-that-transcend-the-divide)
- [Divergences that do not](#divergences-that-do-not)
- [So is there a transcendent pattern?](#so-is-there-a-transcendent-pattern)
- [Sources](#sources)

---

## The unit problem: what maps to what

Almost every viral "LLM vs brain" comparison is a **category error**, and it always
runs the same way: *"GPT-4 has ~1.8 trillion parameters; the human brain has 86
billion neurons — so AI has already surpassed the brain."* This compares two things
that are not the same kind of thing, and picks the pairing that makes the machine
look biggest.

The honest mapping, and the one used throughout this document and its
[graphics](../graphics/brain-vs-ai.html):

| Biological | Artificial | Why they correspond |
|---|---|---|
| **Synapse** | **Parameter (weight)** | Both are the *learned connection strengths* — the thing that changes with experience/training and stores what the system knows. **This is the one defensible scale axis.** |
| Neuron | Activation / hidden unit | Weak analogy: an LLM "neuron" is a scalar in a vector, with none of a real neuron's dendritic computation, spiking, or neuromodulation. |
| — | Token | No biological equivalent; the atom of LLM input/output. |
| Action potential | Forward pass (activation) | Loose functional analogy only. |

So the correct question is not "parameters vs neurons" but **parameters vs
synapses** — and on that axis the popular narrative inverts.

---

## Scale: where LLMs actually sit

Human synapse estimates run **~10¹⁴–10¹⁵** (neocortex alone ≈164 trillion ±17%;
whole adult brain commonly cited at ~100–1000 trillion; ~1,000–10,000 synapses per
neuron, ~7,000 typical). Placed on a shared log axis of *connections*:

| System | Connections (synapses / parameters) | Note |
|---|---|---|
| *C. elegans* | ~7,500 synapses | complete connectome |
| Fruit fly | ~5.4 × 10⁷ synapses | full adult connectome (2024) |
| **BERT-large** | 3.4 × 10⁸ parameters | 2018 |
| **GPT-2** | 1.5 × 10⁹ parameters | 2019 |
| Honeybee | ~1 × 10⁹ synapses | estimate |
| **Chinchilla** | 7 × 10¹⁰ parameters | compute-optimal (2022) |
| **GPT-3** | 1.75 × 10¹¹ parameters | 2020 |
| **Llama 3.1** | 4.05 × 10¹¹ parameters | dense, 2024 |
| **PaLM** | 5.4 × 10¹¹ parameters | 2022 |
| **DeepSeek-V3** | 6.71 × 10¹¹ parameters (37 B active) | MoE, 2024 |
| Mouse | ~1 × 10¹² synapses | |
| **GPT-4** | ~1.8 × 10¹² parameters *(estimated, MoE, ~280 B active)* | unconfirmed |
| Cat | ~1 × 10¹³ synapses | |
| Macaque | ~1 × 10¹⁴ synapses | |
| **Human** | ~1 × 10¹⁴ – 10¹⁵ synapses | ~100 T–1 Q |

**The finding.** Frontier LLMs cluster around the **mouse** connection scale
(~10¹²). Even the largest estimated model (GPT-4, ~1.8 × 10¹²) has roughly as many
weights as a *mouse* brain has synapses — and **~100–1000× fewer than a human**.
GPT-3 sits between a honeybee and a mouse. In raw connection count, today's biggest
artificial "brains" are small-mammal-scale, not human-scale. What is remarkable is
not their size but that **language-level competence emerges at mouse-scale
connectivity at all** — achieved not by matching the brain's hardware but by a
completely different bargain: enormous data and energy (below).

*(MoE caveat: mixture-of-experts models like DeepSeek-V3 and GPT-4 have a large
total parameter count but activate only a fraction per token — 37 B and ~280 B
respectively — so their "effective" connection count per forward pass is lower than
the totals above. Biological brains have no clean equivalent; most synapses are not
active on any given thought either.)*

---

## Patterns that transcend the divide

These are the genuine cross-substrate regularities — properties that show up in
both nervous tissue and transformer weights.

### 1. Scaling laws (the strongest candidate)
Both domains obey **power laws relating scale to capability.**
- **Deep learning:** loss falls as a power law in parameters, data, and compute
  (Kaplan et al. 2020; Hoffmann et al. 2022, "Chinchilla"). Chinchilla's headline —
  ~20 tokens per parameter is compute-optimal — means capability is a smooth,
  predictable function of scale, not a series of one-off tricks.
- **Biology:** cognitive capacity across species tracks not brain mass but the
  number of neurons in the associative forebrain (pallium/cortex) — itself a
  scaling relationship (see the [comparative synthesis](00-comparative-synthesis.md)
  and [graphics](../graphics/README.md)). Cortical neuron count scales with body
  and brain in clade-specific power laws (Herculano-Houzel).

That *both* a evolved network and an engineered one show smooth capability-vs-scale
power laws is the most defensible "transcendent" pattern here: **scale buys
capability predictably in distributed networks, whatever the substrate.**

### 2. Distributed, superposed representation
Neither system stores a concept in one place. Biological brains use **population
codes** — meaning is carried by patterns across many neurons. LLMs use
**distributed embeddings**, and demonstrably pack more features than they have
dimensions via **superposition**. Both are robust to the loss of any single unit;
both resist the "grandmother cell" picture. This is a real structural convergence.

### 3. "More units ≠ more capability"
The collection's central biological lesson — the elephant has 3× the human's total
neurons but ~98% are cerebellar, so raw count misleads — has an exact LLM parallel.
A model's parameter count alone does not determine capability: **architecture, data
quality, and training regime dominate.** Chinchilla (70 B) beat Gopher (280 B) by
training on more data; well-trained small models beat poorly-trained large ones.
In both worlds, *where and how* the connections are used beats *how many*.

### 4. Modular / mixture structure
Brains route information through specialized subsystems; MoE LLMs activate a subset
of "expert" sub-networks per input. A loose but real convergence toward **sparse,
conditional computation** — using only part of the network for any given task.

---

## Divergences that do not

Equally important: the places where the two are *not* alike, and where the analogy
must not be pushed.

### 5. Data efficiency — the largest gap
A human hears/reads on the order of **10⁷–10⁸ words** by adulthood and is fluent.
Frontier LLMs train on **10¹²–1.5 × 10¹³ tokens** — roughly **10⁴–10⁵× more
language** than a human ever encounters, to reach comparable-in-places fluency. The
brain is fantastically more data-efficient. Whatever the brain is doing, it is *not*
what current LLMs do.

### 6. Energy efficiency — the second-largest gap
The human brain runs on **~20 watts, continuously, for a lifetime** (~175 kWh/year).
Training GPT-3 alone consumed **~1,287 MWh** — roughly the brain's output for
**~7,000 years** — as a one-time cost, and inference adds ~0.3 Wh *per query* across
billions of queries. Per unit of capability, biology is orders of magnitude more
efficient. (This is *the* practical argument for neuromorphic and brain-inspired
hardware.)

### 7. Learning paradigm
- **Continual vs frozen.** Brains learn continuously and mostly avoid catastrophic
  forgetting; a deployed LLM's weights are **frozen** — it does not learn from
  conversations (context is not weight change).
- **One-shot vs many-shot.** Brains often learn from a single example; LLMs need
  massive repetition (in-context "learning" is a separate, transient phenomenon).
- **Embodiment & grounding.** Brains are wired to a body sensing and acting in a
  world; LLMs learn from text about the world, not the world. Meaning is grounded
  differently, if at all.
- **Persistent state.** Brains have ongoing internal dynamics and memory; a
  transformer is (mostly) a stateless function of its context window.

### 8. Substrate & mechanism
Spikes vs continuous activations; chemical synapses and neuromodulation vs matrix
multiplies; ~10¹⁵ analog, noisy, self-repairing synapses vs digital deterministic
weights; backpropagation (biologically implausible) vs the brain's unknown, local
learning rules ([doc 14](../docs/14-neural-computation-and-ai.md)). The *hardware*
and the *learning algorithm* are different in kind.

---

## So is there a transcendent pattern?

**Yes — but a narrow, specific one.** What genuinely transcends the biological/
artificial divide is a small set of principles about **distributed networks as an
information-processing medium**:

1. **Capability scales with size as a power law** — predictably, in both evolved
   and engineered networks.
2. **Representation is distributed and superposed** — no single locus, graceful
   degradation, in both.
3. **Organization beats raw count** — architecture, training, and where connections
   are used matter more than how many, in both.

These are properties of *large adaptive networks in general*, which is why they
appear in tissue and in transformers alike. They are the real answer to the user's
question.

**But the divide is also real and deep**, and the pattern does *not* extend to
mechanism, efficiency, or learning. LLMs reach mouse-scale connection counts and,
via 10⁴–10⁵× more data and vastly more energy, extract language-level competence —
a genuinely new kind of system, not a smaller or larger brain. The honest summary:
**brains and LLMs are two very different solutions that happen to share the deep
statistics of scaled distributed computation — and diverge on almost everything
else.** The transcendent pattern is not "they are the same"; it is "the same few
laws of large networks govern both, and then biology and engineering part ways."

A useful mental model: LLMs are not artificial *brains*. They are artificial systems
that, like brains, are large distributed networks — and so inherit the handful of
laws that any such network obeys, while sharing none of the biology.

---

## Sources

- Hoffmann et al., "Training Compute-Optimal Large Language Models" (Chinchilla), 2022 — [arXiv:2203.15556](https://arxiv.org/abs/2203.15556)
- Kaplan et al., "Scaling Laws for Neural Language Models," 2020 — [arXiv:2001.08361](https://arxiv.org/abs/2001.08361)
- DeepSeek-AI, "DeepSeek-V3 Technical Report," 2024 (671 B MoE, 37 B active, 14.8 T tokens) — [arXiv:2412.19437](https://arxiv.org/abs/2412.19437)
- Meta, Llama 3.1 (405 B, 15 T tokens) — [ai.meta.com/blog/meta-llama-3-1](https://ai.meta.com/blog/meta-llama-3-1/)
- Patterson et al., "Carbon Emissions and Large Neural Network Training," 2021 (GPT-3 ≈1,287 MWh) — [arXiv:2104.10350](https://arxiv.org/abs/2104.10350)
- Epoch AI, "How much energy does ChatGPT use?" (≈0.3 Wh/query) — [epoch.ai](https://epoch.ai/gradient-updates/how-much-energy-does-chatgpt-use)
- Human neocortical synapse count (≈164 T ±17%) — [Univ. of South Florida UJMM](https://digitalcommons.usf.edu/ujmm/) ; AI Impacts, "Scale of the Human Brain" — [aiimpacts.org](https://aiimpacts.org/scale-of-the-human-brain/)
- Fruit-fly connectome (~54.5 M synapses), 2024 — [Science News](https://www.sciencenews.org/article/fruit-fly-brain-connections-traced)
- Elhage et al., "Toy Models of Superposition," Anthropic, 2022 — [transformer-circuits.pub](https://transformer-circuits.pub/2022/toy_model/index.html)
- Herculano-Houzel, "The Human Advantage" (neuron-scaling across species), 2016

*Parameter counts for closed models (notably GPT-4) are estimates and unconfirmed;
synapse counts are order-of-magnitude and method-dependent. Educational, not a
definitive ranking.*
