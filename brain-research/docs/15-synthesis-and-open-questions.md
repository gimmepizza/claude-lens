# Synthesis & Open Questions

The preceding fourteen documents each dissect one system of the brain. This
capstone does the opposite: it steps back to name the **principles that recur
across all of them**, and then lays out — honestly — the **big questions the
field has not answered.** If the rest of the collection is the anatomy of what we
know, this is the map of how it connects and where it runs out.

## Table of Contents
- [Ten principles that recur across every system](#ten-principles-that-recur-across-every-system)
- [How the pieces actually interlock](#how-the-pieces-actually-interlock)
- [The major unsolved problems](#the-major-unsolved-problems)
- [How to hold this knowledge](#how-to-hold-this-knowledge)

---

## Ten principles that recur across every system

Read the documents together and the same ideas keep surfacing under different
names. These are the load-bearing concepts — internalize them and most of
neuroscience becomes variations on a theme.

**1. The neuron is the unit, but not a simple one.** Everything runs on cells
that convert graded inputs into all-or-none spikes and communicate chemically at
synapses ([01](01-neurons-and-cells.md)). But a real neuron is not a weighted
sum: its dendrites compute, its output depends on history and neuromodulatory
context, and glia participate actively ([14](14-neural-computation-and-ai.md)).
Every higher function is built from this component, and its subtleties matter.

**2. Excitation and inhibition are held in balance.** Glutamate pushes, GABA
pulls, and the ratio between them is a control variable, not a detail
([03](03-neurotransmitter-systems.md)). Tip it and you get seizures, or the
excitotoxic cell death seen in stroke and neurodegeneration
([07](07-aging-and-neurodegeneration.md)); disturb its development and you get
some of the leading models of autism and schizophrenia
([11](11-disorders-and-mental-illness.md)).

**3. Plasticity is the single most unifying idea.** The rule that co-active
connections strengthen ([04](04-learning-and-memory.md),
[05](05-neuroplasticity.md)) is not just how we learn facts. It is how the
developing brain wires itself, how cortical maps reorganize after injury, how
motor skills consolidate ([10](10-motor-systems.md)), how fear is acquired
*and* extinguished ([06](06-stress-and-fight-or-flight.md)), and how
addiction hijacks the reward system ([11](11-disorders-and-mental-illness.md)).
The same mechanism is the source of both our adaptability and our pathologies.

**4. The brain predicts; it does not merely react.** Perception is as much
top-down inference as bottom-up sensation ([09](09-sensory-systems.md)). The
motor system runs on forward models that anticipate the consequences of action
([10](10-motor-systems.md)). The body's set-points are defended by
*allostasis* — regulation by prediction, not just feedback
([13](13-body-brain-interfaces.md)). Even emotion is increasingly framed as
predictive construction. "The brain is a prediction machine" is the closest thing
the field has to a unifying slogan.

**5. There is no single center for anything.** Function is distributed across
networks, not localized to spots. The amygdala is not "the fear center," the
hippocampus is not a memory warehouse, and no region is the seat of the self
([02](02-anatomy-and-organization.md), [06](06-stress-and-fight-or-flight.md)).
Damage reveals what a region *contributes*, not what it *is for* in isolation.
Beware any "this bit does that" story — the truth is almost always a circuit.

**6. Processing is hierarchical, parallel, and topographic.** Information is
transformed through stages of increasing abstraction (retina → V1 → higher visual
areas), split into parallel streams that are processed simultaneously (the "what"
and "where" pathways), and laid out in ordered maps (retinotopy, tonotopy, the
motor and sensory homunculi). This architecture recurs in every sensory and motor
system ([09](09-sensory-systems.md), [10](10-motor-systems.md)).

**7. Feedback loops and homeostasis are everywhere.** Cortisol shuts off its own
release; firing rates are stabilized by homeostatic scaling; the basal ganglia
gate their own output through opposing pathways. The brain is saturated with
negative-feedback control that keeps it in a working range
([03](03-neurotransmitter-systems.md), [06](06-stress-and-fight-or-flight.md),
[13](13-body-brain-interfaces.md)). When these loops fail, systems run away.

**8. The brain is embodied and embedded.** It is not a computer in a jar. It is
wired bidirectionally to the gut, the immune system, and the endocrine glands
([13](13-body-brain-interfaces.md)); it evolved to control a body moving
through a world; and its computations are shaped by that world
([14](14-neural-computation-and-ai.md)). Cognition without a body is a partial
picture.

**9. Everything costs energy, and energy constrains everything.** The brain is ~2%
of body mass but burns ~20% of its energy, running on roughly 20 watts
([01](01-neurons-and-cells.md)). This budget explains sparse coding, the
vulnerability of neurons to metabolic and vascular failure in aging
([07](07-aging-and-neurodegeneration.md)), and one of the starkest gaps
between brains and today's AI ([14](14-neural-computation-and-ai.md)).

**10. What we know is bounded by how we can measure.** Every fact in this
collection rests on a method with a specific resolution, a specific blind spot,
and a specific confound ([12](12-methods-of-neuroscience.md)). fMRI is
correlational and slow; lesions are imprecise; most causal manipulation happens in
mice. Converging evidence across methods is what turns a finding into knowledge —
and its absence is why so much below is still open.

---

## How the pieces actually interlock

A single concrete thread shows how inseparable these systems are. Consider **what
happens when you learn to fear something:**

1. A stimulus is **transduced and processed** up the sensory hierarchy
   ([09](09-sensory-systems.md)) and, in parallel, routed rapidly toward the
   amygdala for threat evaluation ([06](06-stress-and-fight-or-flight.md)).
2. If it signals danger, the amygdala triggers the **two-wave stress response** —
   the fast adrenaline surge and the slower cortisol wave via the HPA axis
   ([06](06-stress-and-fight-or-flight.md)) — mobilizing the whole body
   through autonomic and endocrine channels ([13](13-body-brain-interfaces.md)).
3. **Glutamatergic transmission and LTP** in the amygdala physically strengthen
   the synapses linking that stimulus to the threat response
   ([03](03-neurotransmitter-systems.md), [04](04-learning-and-memory.md))
   — i.e., plasticity ([05](05-neuroplasticity.md)) writes the association
   into the circuit.
4. **Cortisol modulates that consolidation**, following an inverted-U: the right
   amount sharpens the memory, too much impairs it — which is exactly why extreme
   stress produces the fragmented, over-consolidated memories of trauma
   ([06](06-stress-and-fight-or-flight.md), [11](11-disorders-and-mental-illness.md)).
5. **Sleep consolidates** the new learning overnight
   ([08](08-sleep-consciousness-development.md)).
6. Later, the prefrontal cortex can drive **extinction** — new inhibitory learning
   that suppresses, but does not erase, the fear. When that regulatory circuit is
   weak, the fear persists as an anxiety disorder or PTSD, and *exposure therapy*
   is, mechanistically, extinction training
   ([06](06-stress-and-fight-or-flight.md), [11](11-disorders-and-mental-illness.md)).

Seven "separate" documents describe **one continuous process.** That is the real
lesson of studying the brain system by system: the divisions are ours, not the
brain's.

---

## The major unsolved problems

A reference that only lists what we know is misleading, because the honest state
of neuroscience is that its deepest questions are open. These are the ones that
matter most.

### 1. The neural code
We do not have a general theory of how neurons *represent* information. Is meaning
carried by firing rate, by precise spike timing, by the coordinated activity of
populations, or by all of these depending on context? Without a settled code, we
can record millions of neurons and still not fully *read* them
([01](01-neurons-and-cells.md), [12](12-methods-of-neuroscience.md)).

### 2. How a memory is physically stored — and where
LTP is almost certainly *part* of the story, but the stable, decades-long engram
is not fully explained by synaptic weights alone, which turn over on the scale of
days. Candidate substrates include synaptic configuration, structural connectivity,
neuronal ensembles, and even sub-synaptic or extracellular-matrix mechanisms. How
memory survives molecular turnover is unresolved
([04](04-learning-and-memory.md)).

### 3. Consciousness — the hard problem
No one knows why any physical process should be accompanied by subjective
experience, and no current theory (Global Workspace, Integrated Information,
higher-order theories) is established — IIT was publicly challenged as untestable
in 2023, and a major 2025 adversarial test partially undercut both leading
theories. We can increasingly identify *correlates* of consciousness; we cannot
yet *explain* it ([08](08-sleep-consciousness-development.md)).

### 4. What causes Alzheimer's — and whether we've been treating the right target
The amyloid cascade hypothesis has dominated for decades, yet plaque burden
correlates poorly with symptoms, and anti-amyloid antibodies deliver only modest
benefit. Whether amyloid is the driver, an early trigger, or a downstream marker —
and what role tau, inflammation, and vascular factors play — remains genuinely
contested ([07](07-aging-and-neurodegeneration.md)).

### 5. The biology of mental illness
Psychiatry still has **no validated biological biomarker** for any major disorder.
The "chemical imbalance" story is dead as an explanation, diagnoses are defined by
symptoms rather than mechanisms, and most treatments were discovered empirically.
Why depression, schizophrenia, or bipolar disorder happen — at the level of
circuits and cells — is largely unknown ([11](11-disorders-and-mental-illness.md)).

### 6. How the brain learns so efficiently
Humans learn from one example, keep learning across a lifetime without
catastrophically overwriting old knowledge, and do it on ~20 watts. Backpropagation
— the engine of modern AI — is biologically implausible, and the brain's actual
learning algorithm(s) are not known. This is both a neuroscience question and the
central question of NeuroAI ([14](14-neural-computation-and-ai.md)).

### 7. Volition
The Libet readiness-potential experiments are now widely reinterpreted (the signal
may reflect stochastic accumulation, not a pre-formed decision), so the popular
claim that "neuroscience disproved free will" is not supported. But how the brain
actually initiates voluntary action — and what, mechanistically, a "decision" is —
remains open ([10](10-motor-systems.md)).

### 8. What sleep is fundamentally *for*
We know sleep is essential and that it supports memory consolidation and waste
clearance, but there is no single agreed-upon core function — and even the
direction of sleep-driven glymphatic clearance was disputed by new evidence in
2024 ([08](08-sleep-consciousness-development.md)).

### 9. Bridging the levels
Perhaps the deepest gap: we have detailed accounts at the molecular level and at
the behavioral level, but connecting them — explaining a thought in terms of ions,
or a mental illness in terms of synapses — is largely unsolved. Marr's three levels
of analysis remain more of an aspiration than an achievement
([14](14-neural-computation-and-ai.md), [12](12-methods-of-neuroscience.md)).

### 10. Individual variability and generalization
Most of what we "know" is averaged across subjects and often derived from a handful
of model organisms. How to account for the enormous variation between individual
brains — and when findings in a mouse do and do not transfer to a human — is a
persistent, under-appreciated problem ([12](12-methods-of-neuroscience.md)).

---

## How to hold this knowledge

Three habits of mind make this material genuinely useful rather than a pile of
facts:

- **Think in circuits and loops, not centers.** Whenever you catch yourself saying
  "region X does Y," ask what network X belongs to and what it is receiving from
  and sending to.
- **Track the certainty, not just the claim.** This collection deliberately flags
  what is established, what is a leading-but-contested model, and what is
  preliminary or rodent-only. The distinction is the point: confidently stated
  neuroscience is often the least reliable kind.
- **Follow the mechanism up and down the levels.** The satisfying understanding is
  the one that connects a molecule to a synapse to a circuit to a behavior — and
  that is exactly the connection the field is still building.

The brain is the best-documented object in biology and still one of the least
understood. Holding both of those facts at once is the correct state of knowledge.

---

*This document synthesizes the collection; every claim is developed and sourced in
the topic document it links to.*
