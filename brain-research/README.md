# The Human Brain — A Comprehensive Reference

An in-depth, source-cited reference on how the human brain works, spanning the
full range from single molecules and cells up to memory, emotion, consciousness,
and the decline of the aging brain. Each document is a standalone deep dive
written from web-researched, cross-verified sources, with a linked **Sources**
section at the end.

> Scope: mainstream, well-established neuroscience, with contested or
> actively-debated topics (e.g. adult human neurogenesis, theories of
> consciousness, the amyloid hypothesis) explicitly flagged as such and
> presented as competing views rather than settled fact.

---

## How to use this collection

The documents are numbered as a rough **bottom-up reading path** — from the
biophysics of a single neuron up to whole-brain cognition and its breakdown —
but each one stands on its own and cross-references the others.

| # | Document | What it covers |
|---|----------|----------------|
| 01 | [Neurons & Cellular Neuroscience](docs/01-neurons-and-cells.md) | Neuron anatomy and types, glial cells, myelination, membrane biophysics, the action potential, synaptic transmission, receptors, neuronal metabolism |
| 02 | [Anatomy & Organization](docs/02-anatomy-and-organization.md) | CNS/PNS divisions, meninges/ventricles/CSF, blood-brain barrier and blood supply, brainstem, cerebellum, diencephalon, basal ganglia, limbic system, cortex and the four lobes, lateralization, connectomics |
| 03 | [Neurotransmitter Systems](docs/03-neurotransmitter-systems.md) | Glutamate, GABA/glycine, dopamine, serotonin, norepinephrine, acetylcholine, histamine, neuropeptides, nitric oxide; pathways, receptors, and how drugs act on them |
| 04 | [Learning & Memory](docs/04-learning-and-memory.md) | Memory taxonomy, working memory, the hippocampus and patient H.M., consolidation and sleep, LTP/LTD, engram cells, reconsolidation, forgetting, conditioning, amnesia |
| 05 | [Neuroplasticity & Neurogenesis](docs/05-neuroplasticity.md) | Synaptic/structural/cortical plasticity, critical periods, experience-dependent change, cortical remapping, adult neurogenesis (and the debate), BDNF, recovery after injury, maladaptive plasticity |
| 06 | [Stress & the Fight-or-Flight Response](docs/06-stress-and-fight-or-flight.md) | Autonomic nervous system, the fast SAM axis and slow HPA/cortisol axis, fight/flight/freeze/fawn, the amygdala and fear circuits, allostatic load, chronic-stress harms, vagal tone, theories of emotion |
| 07 | [Aging & Neurodegeneration](docs/07-aging-and-neurodegeneration.md) | Normal brain aging, the molecular hallmarks of aging, the aging→MCI→dementia continuum, Alzheimer's, Parkinson's and other diseases, mechanisms of neuronal death, cognitive reserve and protective factors, the glymphatic system |
| 08 | [Sleep, Consciousness & Development](docs/08-sleep-consciousness-development.md) | Sleep architecture and brain waves, circadian and homeostatic regulation, functions of sleep, attention and executive function, large-scale networks, theories of consciousness, brain development across the lifespan |

---

## The story these documents tell, in brief

**It starts with the neuron.** The brain's ~86 billion neurons are electrochemical
cells. A neuron holds a resting voltage of roughly −70 mV across its membrane,
maintained by ion gradients and the Na⁺/K⁺ pump. When enough excitatory input
pushes it past threshold, voltage-gated channels trigger an **action potential** —
an all-or-none spike that races down the axon (jumping between nodes of Ranvier if
myelinated) and, at the **synapse**, releases neurotransmitters onto the next cell.
Glial cells — astrocytes, oligodendrocytes, microglia — are not passive scaffolding
but active partners in signaling, insulation, immunity, and metabolism. *(See 01.)*

**Those cells are organized into a layered architecture.** Signals flow through the
brainstem, cerebellum, thalamus, basal ganglia, and limbic structures up to the
folded six-layered cortex, whose frontal, parietal, temporal, and occipital lobes
specialize in movement, sensation, language, and perception — wired together by
white-matter tracts into large-scale functional networks. *(See 02.)*

**Communication runs on chemistry.** Fast point-to-point signaling uses glutamate
(excitatory) and GABA (inhibitory), while slower **neuromodulators** — dopamine,
serotonin, norepinephrine, acetylcholine — broadcast tone across whole regions,
shaping reward, mood, arousal, and attention. Nearly every psychoactive drug works
by nudging one of these systems. *(See 03.)*

**The same synapses that transmit also change** — and that change is learning.
**Long-term potentiation** strengthens co-active connections ("cells that fire
together wire together"), the hippocampus binds experiences into new declarative
memories, and sleep helps consolidate them. *(See 04.)* This capacity to rewire —
**neuroplasticity** — reshapes cortical maps with experience, supports recovery
after injury, and, in a limited way, even adds new neurons in adulthood. *(See 05.)*

**The brain also protects the body.** A perceived threat triggers the amygdala and
a two-wave stress response: the fast adrenaline surge of **fight-or-flight** and the
slower cortisol wave of the HPA axis. Acute stress is adaptive; chronic stress
erodes the cardiovascular, immune, and even the hippocampal memory systems. *(See 06.)*

**Over decades, the machinery wears down.** Normal aging brings modest volume loss
and slower processing; disease brings the misfolded proteins and neuronal death of
Alzheimer's, Parkinson's, and related disorders. Reserve built by education,
exercise, sleep, and vascular health measurably buffers the decline. *(See 07.)*

**And underlying it all are the states of the whole system** — the daily cycle of
sleep that clears waste and consolidates memory, the attentional and executive
control of the prefrontal cortex, the networks whose interplay may give rise to
consciousness, and the decades-long developmental program that builds and prunes
the brain from the womb to old age. *(See 08.)*

---

## Notes on sourcing and reliability

- Each document was researched from multiple authoritative sources — including
  **NIH/NCBI/PubMed Central, NINDS, the National Institute on Aging**, peer-reviewed
  reviews in *Nature*, *Cell*, *Physiological Reviews*, *Frontiers*, and *PNAS*, plus
  reputable references (StatPearls, Kenhub, Britannica, Wikipedia as an entry point).
- Key facts were cross-checked across sources; every document ends with a linked
  **Sources** list.
- This material is **educational**, not medical advice. Neuroscience is a fast-moving
  field and some numbers (e.g. neuron counts, timelines) are best-estimate ranges,
  not fixed constants.

---

## Repository status

This collection currently lives on the working branch
`claude/human-brain-research-g2tdhu` inside the `claude-lens` repository, under the
self-contained `brain-research/` directory. It was intended to be a **standalone
private repository**; the folder is deliberately portable, so it can be lifted out
and pushed to a dedicated private repo at any time (`cd brain-research && git init`,
add a remote, push).
