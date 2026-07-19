# Neurons and Cellular Neuroscience

The nervous system is built from two great classes of cells: **neurons**, the electrically
excitable signaling cells that receive, integrate, and transmit information, and **glia**, the
supporting cells that outnumber or roughly match neurons and that insulate, nourish, defend, and
regulate them. This document is a mechanistic reference on the cellular building blocks of the
nervous system — the anatomy and classification of neurons, the diversity and duties of glial
cells, the biophysics of the membrane at rest, the action potential, chemical and electrical
synaptic transmission, postsynaptic integration, and the extraordinary energy demands that keep it
all running. Approximate quantitative values are given throughout (for example, the resting
membrane potential of a typical neuron is about **−70 mV**); real cells vary, and the numbers are
order-of-magnitude anchors rather than universal constants.

---

## Table of Contents

1. [Neuron Anatomy](#1-neuron-anatomy)
2. [Classification of Neurons](#2-classification-of-neurons)
3. [Glial Cells](#3-glial-cells)
4. [Myelination and Saltatory Conduction](#4-myelination-and-saltatory-conduction)
5. [Membrane Biophysics and the Resting Potential](#5-membrane-biophysics-and-the-resting-potential)
6. [The Action Potential](#6-the-action-potential)
7. [Synaptic Transmission](#7-synaptic-transmission)
8. [Neurotransmitter Receptors and Synaptic Integration](#8-neurotransmitter-receptors-and-synaptic-integration)
9. [Neuronal Metabolism and Energy Demands](#9-neuronal-metabolism-and-energy-demands)
10. [Sources](#sources)

---

## 1. Neuron Anatomy

A neuron is a polarized cell: it has an input end, an integrating region, and an output end, and
its internal machinery is organized to move signals in one direction — from dendrites to soma to
axon to synaptic terminals. This functional polarity is mirrored by anatomical compartments, each
with a distinctive molecular and cytoskeletal signature.

### 1.1 Soma (Cell Body)

The **soma**, or perikaryon, is the bulbous central region containing the nucleus and the bulk of
the biosynthetic machinery — rough endoplasmic reticulum (in neurons the stacked rough ER and free
ribosomes are visible as **Nissl bodies**), Golgi apparatus, mitochondria, and lysosomes. The soma
of a typical mammalian neuron is roughly **10–25 µm** in diameter, though it ranges from ~5 µm for
small granule cells to ~100 µm for large motor neurons. Because most protein and membrane synthesis
occurs here, the soma is the metabolic and trophic hub that supplies the far reaches of the axon and
dendrites via active transport.

### 1.2 Dendrites and Dendritic Spines

**Dendrites** are tapering, branching processes that emanate from the soma and form the primary
receptive surface of the neuron. A single neuron may bear a **dendritic tree** (arbor) that
collects synaptic inputs from hundreds to tens of thousands of other neurons; a cortical pyramidal
cell can receive on the order of **10,000–30,000** synapses. Dendrites contain ribosomes (allowing
local protein synthesis), microtubules, and, importantly, no myelin. The passive and active
properties of the dendritic membrane shape how distributed inputs are filtered and summed before
reaching the soma.

**Dendritic spines** are tiny (~0.5–2 µm) mushroom-, thin-, or stubby-shaped membrane protrusions
that stud the dendrites of many excitatory neurons. Each spine typically hosts a single excitatory
(glutamatergic) synapse and consists of a bulbous **head** connected to the dendritic shaft by a
thin **neck**. The narrow neck electrically and biochemically isolates the spine head, creating a
compartment in which calcium and signaling molecules can rise sharply and locally. Spines are
highly dynamic — they grow, shrink, appear, and retract over minutes to days — and this
**structural plasticity** is a physical substrate of learning and memory.

### 1.3 Axon Hillock and Axon Initial Segment

The **axon hillock** is the cone-shaped region where the axon emerges from the soma. It is largely
free of Nissl substance (ribosomes) and, together with the adjacent **axon initial segment (AIS)**,
contains an exceptionally high density of **voltage-gated Na⁺ channels**. This makes the AIS the
zone of lowest threshold in the neuron — the **spike initiation site** where the summed synaptic
input, having spread from dendrites and soma, is converted into an all-or-none action potential
if it exceeds threshold. The hillock is therefore the neuron's decision point.

### 1.4 Axon and Axon Terminals

The **axon** is a single, usually long process specialized to conduct action potentials away from
the soma toward target cells. Axons vary enormously in length — from a fraction of a millimeter for
local interneurons to more than a meter for motor axons running from the spinal cord to the foot.
An axon may branch into **collaterals** and typically ends in a spray of fine branches (the
**telodendria**) tipped by **axon terminals** (synaptic boutons, or terminal boutons). Each bouton
is packed with synaptic vesicles and mitochondria and forms the presynaptic element of a synapse.
Some terminals are **en passant** ("in passing") boutons — swellings along the axon that make
synapses without terminating it.

### 1.5 Cytoskeleton

The neuronal cytoskeleton provides mechanical support, defines compartment identity, and lays the
tracks for intracellular transport. It has three main filament systems:

| Element | Diameter | Composition | Roles in the neuron |
|---|---|---|---|
| **Microtubules** | ~25 nm | α/β-tubulin heterodimers | Polar tracks for motor-driven transport; structural backbone of axon and dendrites |
| **Neurofilaments** | ~10 nm | Neuron-specific intermediate filaments | Determine axon caliber (larger diameter → faster conduction); tensile strength |
| **Microfilaments** | ~7 nm | Filamentous (F-)actin | Enriched in spines, growth cones, and the sub-membrane cortex; drives shape change and motility |

A defining feature is **microtubule polarity**. In the **axon**, microtubules are uniformly
oriented with their fast-growing **plus ends pointing away from the soma** (toward the terminal),
whereas in **dendrites** microtubule orientation is mixed. This polarity is the reason cargoes sort
correctly, because the two families of motor proteins read microtubule direction. A periodic,
ring-like actin/spectrin lattice wraps the axon at ~190 nm intervals and gives it elasticity and
stability.

### 1.6 Axonal Transport

Because the axon has little capacity for protein synthesis, materials made in the soma must be
delivered along the axon, and worn-out or signaling cargoes must be returned. This is
**axonal transport**, carried out by ATP-powered motor proteins walking along microtubules:

- **Anterograde transport** (soma → terminal) is driven mainly by **kinesin** motors, which walk
  toward microtubule plus ends. It supplies the distal axon and synapse with newly synthesized
  proteins, lipids, synaptic-vesicle precursors, and mitochondria.
- **Retrograde transport** (terminal → soma) is driven by **cytoplasmic dynein**, which walks
  toward microtubule minus ends. It returns aged organelles and misfolded proteins for degradation
  and carries **signaling endosomes** (e.g., neurotrophins such as NGF captured at the terminal)
  that inform the soma about the state of the distal axon.

Transport occurs at two broad speeds: **fast axonal transport** (~50–400 mm/day, for
membranous organelles and vesicles) and **slow axonal transport** (~0.2–8 mm/day, for cytoskeletal
proteins and cytosolic enzymes). Kinesin and dynein act interdependently — many cargoes carry both
motors and switch net direction depending on which is engaged. Disruption of axonal transport is
implicated in neurodegenerative diseases, and this is intuitive given that the longest axons must
sustain a cytoplasmic volume thousands of times larger than the soma.

---

## 2. Classification of Neurons

Neurons are classified along three complementary axes: **function** (direction of information
flow), **structure** (number of processes leaving the soma), and **neurochemistry** (the
transmitter they release). A single neuron carries a label on each axis — for example, a spinal
motor neuron is functionally a motor neuron, structurally multipolar, and neurochemically
cholinergic.

### 2.1 By Function

| Functional class | Direction of signal | Typical location | Notes |
|---|---|---|---|
| **Sensory (afferent)** | Periphery → CNS | Dorsal root & cranial ganglia | Carry information from sensory receptors; often pseudounipolar or bipolar |
| **Motor (efferent)** | CNS → effectors | Ventral horn of spinal cord, brainstem | Drive muscles and glands; multipolar |
| **Interneuron (association)** | Neuron → neuron within CNS | Brain and spinal cord | The vast majority of CNS neurons; mediate reflexes, integration, and computation |

### 2.2 By Structure

Structural class is defined by the number of **neurites** (processes) projecting from the cell body:

| Structural type | Processes from soma | Example / location |
|---|---|---|
| **Unipolar** | One process that branches | Invertebrate neurons; some CNS cells |
| **Pseudounipolar** | Single stalk that splits into two axonal branches (one to periphery, one to CNS) | Dorsal root ganglion sensory neurons |
| **Bipolar** | Two: one axon + one dendrite | Retina, olfactory epithelium, vestibulocochlear (inner ear) |
| **Multipolar** | One axon + many dendrites | Most CNS neurons — motor neurons, pyramidal cells, Purkinje cells |

**Multipolar** neurons are by far the most common in the mammalian CNS. **Pseudounipolar**
neurons are a specialization for sensation: the peripheral and central branches function together
as one long axon, so an action potential generated at a sensory ending can travel toward the CNS
largely bypassing the soma. **Bipolar** neurons are comparatively rare and are concentrated in
special sensory systems.

### 2.3 By Neurotransmitter (Neurochemical Class)

Neurons are also named for the principal transmitter they synthesize and release. Major classes
and their dominant functional flavor:

| Transmitter | Neuron label | Chemical class | Predominant action |
|---|---|---|---|
| **Glutamate** | Glutamatergic | Amino acid | Principal **excitatory** transmitter of the CNS |
| **GABA (γ-aminobutyric acid)** | GABAergic | Amino acid | Principal **inhibitory** transmitter of the brain |
| **Glycine** | Glycinergic | Amino acid | Major inhibitory transmitter of the spinal cord/brainstem |
| **Acetylcholine (ACh)** | Cholinergic | Ester (amine-like) | Neuromuscular junction, autonomic ganglia; excitatory or modulatory |
| **Dopamine** | Dopaminergic | Monoamine (catecholamine) | Reward, movement, motivation (modulatory) |
| **Norepinephrine** | Noradrenergic | Monoamine (catecholamine) | Arousal, attention (modulatory) |
| **Serotonin (5-HT)** | Serotonergic | Monoamine (indoleamine) | Mood, sleep, appetite (modulatory) |
| **Neuropeptides** (e.g., substance P, enkephalins, oxytocin) | Peptidergic | Peptides | Slow, long-lasting modulation; often co-released |

Two caveats: (1) whether a transmitter is excitatory or inhibitory ultimately depends on the
**receptor** on the postsynaptic cell, not just the molecule; ACh, for instance, excites skeletal
muscle but slows the heart. (2) Many neurons **co-release** more than one transmitter (for example,
a fast amino-acid transmitter together with a slow neuropeptide).

---

## 3. Glial Cells

Glia (from the Greek for "glue") are the non-neuronal cells of the nervous system. Far from being
passive packing material, they actively shape neuronal development, insulate axons, buffer the
extracellular environment, defend against injury, and participate directly in synaptic signaling.
They are broadly divided into **macroglia** (astrocytes, oligodendrocytes, Schwann cells) and
**microglia**, with ependymal cells and radial glia rounding out the set.

### 3.1 Astrocytes

Star-shaped cells of the CNS and the most abundant glia. Their many functions include:

- **Ionic homeostasis** — buffering extracellular **K⁺** (which accumulates during firing) and
  regulating pH and osmolarity.
- **Neurotransmitter clearance** — high-affinity transporters (e.g., **EAAT** glutamate
  transporters) rapidly remove glutamate from the synaptic cleft, terminating signaling and
  preventing excitotoxicity; glutamate is recycled via the **glutamate–glutamine cycle**.
- **Metabolic support** — astrocyte **endfeet** wrap capillaries, take up glucose, and can supply
  neurons with **lactate** (the astrocyte–neuron lactate shuttle).
- **Blood–brain barrier** — endfeet induce and maintain the tight-junction barrier of brain
  endothelium.
- **Tripartite synapse** — astrocytes ensheathe synapses and respond to and release signaling
  molecules (**gliotransmitters**), modulating transmission.
- **Structural scaffolding** and formation of the **glial scar** after injury.

### 3.2 Oligodendrocytes

The **myelinating glia of the CNS**. A single oligodendrocyte extends multiple processes and can
myelinate segments of **many (up to ~50) different axons** simultaneously. The myelin they produce
insulates axons and enables fast saltatory conduction (Section 4).

### 3.3 Schwann Cells

The myelinating glia of the **PNS**. In contrast to oligodendrocytes, each **myelinating Schwann
cell** wraps **one internode of one axon**. Along small-diameter unmyelinated axons, a single
**non-myelinating (Remak) Schwann cell** instead cradles several axons in separate grooves. Schwann
cells also guide and support axon **regeneration** after peripheral nerve injury — a capacity the
CNS largely lacks.

### 3.4 Microglia

The resident **immune cells** of the CNS, derived from the same lineage as macrophages. In the
healthy brain they are highly ramified "surveillant" cells constantly probing their surroundings.
Upon injury or infection they activate, migrate, proliferate, and phagocytose debris, dead cells,
and pathogens, and release cytokines. During development and in the mature brain they perform
**synaptic pruning** — physically eliminating weak or unnecessary synapses — which sculpts circuits.

### 3.5 Ependymal Cells

Ciliated epithelial cells that line the **ventricles** of the brain and the **central canal** of
the spinal cord. Specialized ependymal cells of the **choroid plexus** produce **cerebrospinal
fluid (CSF)**, and the beating of ependymal cilia helps circulate it. They form a regulated
interface between CSF and brain tissue.

### 3.6 Radial Glia

Elongated cells prominent in the **developing** nervous system. They serve two key roles:
(1) as **neural progenitors**, dividing to generate neurons, astrocytes, and oligodendrocytes; and
(2) as **migration guides** — their long radial fibers span the developing cortical wall and act as
scaffolds along which newborn neurons climb to their final positions. Most radial glia are
transient, though some persist as adult stem cells (e.g., in the hippocampal dentate gyrus and the
subventricular zone).

---

## 4. Myelination and Saltatory Conduction

### 4.1 Myelin

**Myelin** is a lipid-rich, multilamellar sheath formed by the tightly wrapped plasma membranes of
oligodendrocytes (CNS) or Schwann cells (PNS). Its ~70–80% lipid content makes it an excellent
electrical **insulator**: it increases membrane resistance and dramatically reduces membrane
capacitance, so less charge leaks across and less is needed to change the voltage of the underlying
axon. Myelin is deposited in segments called **internodes**, each up to ~1 mm long.

### 4.2 Nodes of Ranvier

Between successive internodes are short (~1 µm) unmyelinated gaps called **nodes of Ranvier**. The
nodal axon membrane is densely populated with **voltage-gated Na⁺ channels** (and, flanking them in
the juxtaparanode, K⁺ channels). Because the internodal membrane is insulated and channel-poor, the
action potential can only regenerate at the nodes.

### 4.3 Saltatory Conduction

In a myelinated axon the current entering at one node spreads **passively (electrotonically)** down
the low-capacitance internode to the next node, where the concentrated Na⁺ channels regenerate a
full-amplitude action potential. The impulse thus appears to **jump from node to node** — hence
*saltatory* (Latin *saltare*, "to leap") conduction. The consequences:

- **Speed**: conduction velocity increases by roughly an order of magnitude. Large myelinated human
  axons conduct at up to **~120 m/s**, whereas thin unmyelinated axons conduct at only
  **~0.5–2 m/s**. Velocity scales with axon diameter and degree of myelination.
- **Energy efficiency**: because Na⁺/K⁺ fluxes (which must later be pumped back) occur only at the
  small nodal patches rather than continuously along the whole membrane, far less ATP is spent per
  impulse.
- **Space efficiency**: myelination achieves high speeds without the enormous diameters that
  unmyelinated axons would require (the invertebrate solution is the giant axon).

Demyelinating diseases such as **multiple sclerosis** (CNS) and **Guillain–Barré syndrome** (PNS)
degrade myelin, slowing or blocking conduction and producing the corresponding neurological
deficits.

---

## 5. Membrane Biophysics and the Resting Potential

### 5.1 The Membrane as a Capacitor with Batteries

The neuronal plasma membrane is a thin lipid bilayer that is essentially impermeable to ions,
studded with protein channels and pumps. It behaves electrically like a **capacitor** (the bilayer
stores charge) in parallel with **resistors and batteries** (the ion channels, each with a
"battery" set by that ion's electrochemical gradient). At rest there is a steady voltage across it,
the **resting membrane potential (RMP)**, typically about **−65 to −70 mV** (inside negative
relative to outside).

### 5.2 Ion Gradients

The RMP arises from unequal ion distributions actively maintained across the membrane. Approximate
mammalian concentrations (mM):

| Ion | Extracellular | Intracellular | Equilibrium potential (E_ion, ~37 °C) |
|---|---|---|---|
| **K⁺** | ~4–5 | ~140 | **≈ −90 mV** |
| **Na⁺** | ~145 | ~12–15 | **≈ +60 mV** |
| **Cl⁻** | ~110 | ~5–10 | **≈ −65 mV** |
| **Ca²⁺** | ~1–2 | ~0.0001 (100 nM) | **≈ +120 to +140 mV** |

K⁺ is concentrated inside; Na⁺, Cl⁻, and Ca²⁺ are concentrated outside. Large impermeant
intracellular anions (proteins, phosphates) also contribute to the charge balance.

### 5.3 The Nernst Equation (conceptual)

For a single permeant ion, the **equilibrium (Nernst) potential** is the membrane voltage at which
the **electrical** force on the ion exactly balances its **concentration (diffusional)** force, so
there is zero net flux. Conceptually:

> E_ion = (RT / zF) · ln([ion]_out / [ion]_in)

At body temperature this reduces to the convenient form **E = (61.5 mV / z) · log₁₀([out]/[in])**,
where *z* is the ion's charge. Thus the steep outward K⁺ gradient gives E_K ≈ −90 mV, and the
inward Na⁺ gradient gives E_Na ≈ +60 mV. Each ion "wants" to pull the membrane toward its own
equilibrium potential.

### 5.4 The Goldman–Hodgkin–Katz Equation (conceptual)

Real membranes are permeable to several ions at once, so the resting potential is a **weighted
average** of the individual equilibrium potentials, weighted by each ion's **permeability**. This is
captured by the **Goldman–Hodgkin–Katz (GHK) equation**, which combines the concentrations and
relative permeabilities of Na⁺, K⁺, and Cl⁻. The key insight: **at rest the membrane is far more
permeable to K⁺ than to Na⁺** (P_K ≫ P_Na, roughly 25–40:1 through leak channels). The resting
potential therefore sits close to E_K (~−90 mV) but is pulled a bit positive by the small resting
Na⁺ leak, landing near **−70 mV**. During an action potential the permeabilities reverse, and the
same logic drives the voltage toward E_Na.

### 5.5 The Na⁺/K⁺-ATPase

Ion gradients would eventually dissipate through leak channels were they not continuously restored.
The **sodium–potassium pump (Na⁺/K⁺-ATPase)** hydrolyzes one **ATP** to export **3 Na⁺** and import
**2 K⁺** per cycle, working against both gradients. Because it moves **3 positive charges out for
every 2 in**, it is **electrogenic**, contributing a few millivolts of negativity directly, but its
principal role is to **maintain the gradients** that the Nernst/GHK relations depend on. This pump
is a major consumer of neuronal ATP (Section 9).

### 5.6 Ion Channels

Ion channels are membrane proteins forming aqueous, often ion-selective pores. Three broad
functional categories are central to neuronal signaling:

- **Leak (passive) channels** — open at rest, largely responsible for resting permeability. K⁺
  leak channels dominate and set the RMP near E_K.
- **Voltage-gated channels** — open/close in response to changes in membrane potential; the Na⁺,
  K⁺, and Ca²⁺ voltage-gated channels underlie the action potential and transmitter release.
- **Ligand-gated channels (ionotropic receptors)** — open when a chemical (neurotransmitter) binds;
  they mediate fast synaptic potentials (Section 8).

(Additional gating modes exist, e.g., mechanically gated channels in sensory endings and
second-messenger–gated channels.)

---

## 6. The Action Potential

The **action potential (AP)** is a brief, self-regenerating, all-or-none reversal of membrane
polarity that carries signals rapidly along the axon. In neurons it lasts about **1–2 ms**.

### 6.1 Threshold and the All-or-None Principle

Subthreshold depolarizations decay passively. But if a stimulus depolarizes the axon initial
segment to about **−55 mV** (the **threshold**), enough voltage-gated Na⁺ channels open to create a
self-reinforcing (regenerative) loop: Na⁺ entry depolarizes further, which opens more Na⁺ channels.
The AP is therefore **all-or-none** — once threshold is crossed the spike fires with a stereotyped
amplitude and shape independent of stimulus strength. Stimulus intensity is encoded not by AP size
but by **firing frequency** (rate coding) and by the number of neurons recruited.

### 6.2 Phases and Their Molecular Basis

| Phase | Voltage change | Molecular events |
|---|---|---|
| **Resting** | ~ −70 mV | K⁺ leak dominates; Na⁺ channels closed but activatable |
| **Depolarization (rising)** | −55 → ~ +30/+40 mV | Voltage-gated **Na⁺ channels open** (activation gate *m*); Na⁺ rushes in; regenerative |
| **Peak / overshoot** | ~ +30 to +40 mV | Na⁺ channels **inactivate** (inactivation gate *h* closes); voltage nears E_Na then halts |
| **Repolarization (falling)** | +40 → −70 mV | Voltage-gated **K⁺ channels** (delayed rectifiers) open; K⁺ flows out |
| **Hyperpolarization (undershoot)** | dips to ~ −80/−90 mV | Slow K⁺ channels still open; membrane briefly overshoots toward E_K |
| **Return to rest** | → −70 mV | K⁺ channels close; leak conductances and the pump restore RMP |

The elegance of the mechanism lies in the **two gates of the voltage-gated Na⁺ channel**: a fast
**activation gate** that opens on depolarization and a slower **inactivation gate** that then
swings shut over the pore. In the Hodgkin–Huxley framework, Na⁺ conductance ∝ *m³h* — rising as *m*
opens, then falling as *h* closes. K⁺ channels open more slowly (conductance ∝ *n⁴*) and lack fast
inactivation, so they dominate during repolarization.

### 6.3 Refractory Periods

- **Absolute refractory period** — during depolarization and early repolarization, Na⁺ channel
  inactivation gates are shut. **No stimulus, however strong, can trigger a second AP.** This caps
  the maximum firing rate and, crucially, ensures the impulse travels in **one direction** (it
  cannot re-excite the region it just left).
- **Relative refractory period** — as inactivation gates reopen and K⁺ channels remain partly open
  (membrane hyperpolarized), a **stronger-than-normal** stimulus can elicit an AP. Excitability
  gradually returns to baseline.

### 6.4 Propagation

The local inward current at an active patch depolarizes the adjacent membrane to threshold,
regenerating the AP there — a chain reaction down the axon. Because the region just behind is
refractory, propagation is unidirectional (orthodromic, soma → terminal). In **unmyelinated** axons
this occurs continuously and relatively slowly; in **myelinated** axons it proceeds by fast
**saltatory conduction** from node to node (Section 4). Conduction velocity increases with axon
diameter (lower internal resistance) and with myelination.

---

## 7. Synaptic Transmission

A **synapse** is the specialized junction where a neuron communicates with a target cell. There are
two fundamental kinds: **chemical synapses**, which use neurotransmitter molecules and predominate
in the vertebrate nervous system, and **electrical synapses**, which pass current directly.

### 7.1 Chemical Synapses: Overview

A chemical synapse has three parts: the **presynaptic terminal** (containing neurotransmitter-filled
vesicles and an **active zone** for release), the **synaptic cleft** (a gap of roughly **20–40 nm**),
and the **postsynaptic membrane** (studded with receptors, often thickened into a
**postsynaptic density**). Transmission is a molecular relay: an electrical signal is converted to a
chemical one and back to an electrical one, with a characteristic **synaptic delay of ~0.5–1 ms**.

### 7.2 Steps of Chemical Transmission

1. **AP invades the terminal.** The action potential depolarizes the presynaptic bouton.
2. **Ca²⁺ influx.** Depolarization opens **voltage-gated Ca²⁺ channels** clustered at the active
   zone. Because intracellular Ca²⁺ is extraordinarily low (~100 nM) and the driving force is huge,
   Ca²⁺ floods in, creating brief, steep local microdomains of high Ca²⁺.
3. **Ca²⁺ sensing.** **Synaptotagmin**, a Ca²⁺-binding protein on the vesicle, acts as the fast
   **calcium sensor** that triggers fusion.
4. **Vesicle fusion via SNAREs.** Docked, primed vesicles fuse with the membrane through the
   **SNARE complex**: the vesicle (v-SNARE) protein **synaptobrevin/VAMP** zippers together with the
   target-membrane (t-SNARE) proteins **syntaxin** and **SNAP-25**. Ca²⁺-bound synaptotagmin
   (aided by **complexin**) triggers this zippered complex to drive **exocytosis**.
5. **Neurotransmitter release.** Vesicle contents (thousands of transmitter molecules per vesicle —
   a "quantum") are released into the cleft and diffuse across it in microseconds.
6. **Receptor binding.** Transmitter binds postsynaptic **receptors**, opening ion channels
   (ionotropic) or launching second-messenger cascades (metabotropic), producing a postsynaptic
   potential.
7. **Signal termination / clearance.** The transmitter is removed by (a) **reuptake** via
   transporters into the presynaptic terminal or glia (e.g., dopamine and serotonin transporters,
   astrocytic glutamate transporters), (b) **enzymatic degradation** in the cleft (e.g.,
   **acetylcholinesterase** hydrolyzing ACh), and/or (c) simple **diffusion** away from the synapse.
8. **Vesicle recycling.** Fused membrane is retrieved (e.g., by clathrin-mediated endocytosis) and
   refilled with transmitter for reuse.

The SNARE machinery is the target of potent toxins: **botulinum** and **tetanus** neurotoxins are
proteases that cleave SNARE proteins, blocking release and causing paralysis.

### 7.3 Electrical Synapses (Gap Junctions)

At an **electrical synapse**, the pre- and postsynaptic membranes are bridged by **gap junctions** —
paired hemichannels (**connexons**, each built of six **connexin** subunits) that align to form
open pores connecting the two cytoplasms. Ions and small molecules pass directly, so current flows
from one cell to the next with **essentially no synaptic delay**. Compared with chemical synapses,
electrical synapses are:

| Property | Electrical synapse | Chemical synapse |
|---|---|---|
| **Gap width** | ~3.5 nm (gap junction) | ~20–40 nm (cleft) |
| **Delay** | Virtually none | ~0.5–1 ms |
| **Direction** | Usually bidirectional | Unidirectional |
| **Signal** | Direct ionic current | Neurotransmitter |
| **Plasticity/gain** | Limited; fast, faithful | Can amplify, integrate, invert (excite or inhibit), and be modulated |

Electrical synapses excel at **speed and synchrony** — synchronizing populations of interneurons
and enabling escape reflexes — whereas chemical synapses provide the amplification, sign inversion,
and plasticity that underlie complex computation and learning.

---

## 8. Neurotransmitter Receptors and Synaptic Integration

### 8.1 Ionotropic vs Metabotropic Receptors

Postsynaptic receptors fall into two mechanistic families:

| Feature | **Ionotropic** (ligand-gated ion channel) | **Metabotropic** (G-protein-coupled receptor) |
|---|---|---|
| Mechanism | Transmitter binding directly opens an integral ion channel | Binding activates a G protein → second messengers → downstream effectors |
| Speed of onset | Fast (~ms) | Slow (tens of ms to seconds) |
| Duration | Brief | Prolonged, can outlast the stimulus |
| Effect | Direct EPSP/IPSP | Modulatory: open/close distant channels, alter enzymes, change gene expression |
| Examples | AMPA, NMDA, kainate (glutamate); nicotinic ACh; GABA_A; glycine | mGluR (glutamate); muscarinic ACh; GABA_B; most dopamine, serotonin, adrenergic receptors |

Ionotropic receptors mediate **fast, point-to-point** transmission; metabotropic receptors mediate
**slow, diffuse neuromodulation** and can amplify a signal enormously via enzymatic cascades. The
**NMDA receptor** is a notable ionotropic hybrid: it is both ligand- and voltage-gated (blocked by
Mg²⁺ at rest) and admits Ca²⁺, making it a molecular **coincidence detector** central to synaptic
plasticity (long-term potentiation).

### 8.2 EPSPs and IPSPs

The postsynaptic response depends on which ions the opened channels admit:

- **Excitatory postsynaptic potential (EPSP)** — a local **depolarization** that moves the membrane
  **toward threshold**, increasing the probability of firing. Typically produced by opening
  cation-permeable channels (Na⁺/K⁺, sometimes Ca²⁺), e.g., glutamate acting on AMPA receptors.
- **Inhibitory postsynaptic potential (IPSP)** — a local **hyperpolarization** (or a
  shunting/stabilization near rest) that moves the membrane **away from threshold**, decreasing
  firing probability. Typically produced by opening **Cl⁻** channels (GABA_A, glycine) or K⁺
  channels (GABA_B).

Individual EPSPs are small (often **~0.1–1 mV** at a single synapse) and decay as they spread
toward the soma — far below the ~15 mV swing needed to reach threshold from rest.

### 8.3 Spatial and Temporal Summation

Because single synaptic potentials are tiny, a neuron must **integrate** many inputs to decide
whether to fire. This occurs at the axon initial segment, which continuously sums the graded
potentials arriving from across the dendritic tree:

- **Spatial summation** — postsynaptic potentials from **different synapses**, arriving at nearly
  the **same time** across the dendrites, add together. Summation *in space*.
- **Temporal summation** — successive potentials from the **same synapse** arriving in **rapid
  succession** overlap before each decays, adding together. Summation *in time*.

EPSPs and IPSPs sum **algebraically**: coincident excitation and inhibition can cancel. If the net
depolarization at the initial segment reaches **threshold (~−55 mV)**, an action potential fires.
The neuron is thus a **spatiotemporal integrator** — a leaky summing device that converts thousands
of graded, distributed synaptic inputs into a digital train of all-or-none output spikes. Metabotropic
inputs, being slow and long-lasting, are especially effective substrates for **temporal summation**
and for setting the background excitability over which fast ionotropic signals ride.

---

## 9. Neuronal Metabolism and Energy Demands

### 9.1 A Uniquely Energy-Hungry Organ

The brain is metabolically extravagant: in humans it is only **~2% of body mass** yet consumes
about **~20% of the body's resting oxygen and glucose**. **Glucose** is the brain's near-obligatory
fuel under normal conditions; full oxidative metabolism of one glucose molecule yields roughly
**30–36 ATP**. During prolonged fasting the brain can adapt to burn **ketone bodies**, and neurons
can also use **lactate** (notably supplied by astrocytes) as a substrate.

### 9.2 Where the ATP Goes

The dominant cost is **electrical signaling** — restoring the ion gradients disturbed by synaptic
and action potentials. Estimates attribute roughly **~70–80%** of neuronal ATP use to
signaling-related processes, with the remainder covering housekeeping (biosynthesis, transport,
maintenance). The major sinks:

- **Reversing postsynaptic ion fluxes** — pumping back the Na⁺ (and Ca²⁺) that entered through
  postsynaptic receptors; in glutamatergic circuits this is the single largest expense.
- **Action potentials** — restoring Na⁺/K⁺ gradients disturbed by each spike via the
  **Na⁺/K⁺-ATPase**.
- **Maintaining the resting potential** — the continual pump activity that counters leak currents.
- **Neurotransmitter cycling, vesicle loading, and Ca²⁺ extrusion**, plus axonal transport.

Because signaling dominates the bill, **excitatory (glutamatergic) neurons** account for the large
majority of the calculated ATP use, while inhibitory neurons and glia take a smaller share.

### 9.3 Consequences of High Demand and Low Reserve

Neurons store **very little energy** (negligible glycogen; glycogen is held mainly in astrocytes)
and depend on **continuous** delivery of oxygen and glucose from the blood. Consequently:

- The brain is exquisitely vulnerable to **ischemia and hypoxia** — a few minutes of interrupted
  blood flow causes pump failure, gradient collapse, depolarization, glutamate excitotoxicity, and
  neuronal death.
- Neuronal activity is tightly coupled to **local blood flow** (neurovascular coupling), the basis
  of functional imaging signals such as **fMRI BOLD**.
- **Mitochondria** are actively trafficked to high-demand sites — synaptic terminals and nodes of
  Ranvier — to meet local ATP needs, one more reason axonal transport is indispensable.

---

## Sources

- [Organization of Cell Types — Neuroscience Online, UT Houston](https://nba.uth.tmc.edu/neuroscience/m/s1/chapter08.html)
- [Histology, Axon — StatPearls (NCBI Bookshelf)](https://www.ncbi.nlm.nih.gov/books/NBK554388/)
- [Axon — Wikipedia](https://en.wikipedia.org/wiki/Axon)
- [Axonal transport — Wikipedia](https://en.wikipedia.org/wiki/Axonal_transport)
- [Anterograde and Retrograde Transport Mechanisms in Neurons — Pressbooks](https://uen.pressbooks.pub/expertneuro/chapter/anterograde-and-retrograde-transport-mechanisms-in-neurons/)
- [Neuron Structure and Classification — BYU-Idaho](https://content.byui.edu/file/a236934c-3c60-4fe9-90aa-d343b3e3a640/1/module6/readings/neuron_structure.html)
- [Structural Diversity of Neurons — Medicine LibreTexts](https://med.libretexts.org/Bookshelves/Anatomy_and_Physiology/Anatomy_and_Physiology_(Boundless)/10:_Overview_of_the_Nervous_System/10.3:_Neurons/10.3A:_Structural_Diversity_of_Neurons)
- [Unipolar vs. bipolar vs. multipolar neurons — Medical News Today](https://www.medicalnewstoday.com/articles/unipolar-vs-bipolar-vs-multipolar-neurons)
- [Types of neurons — Queensland Brain Institute](https://qbi.uq.edu.au/brain/brain-anatomy/types-neurons)
- [Two Major Categories of Neurotransmitters — Neuroscience (NCBI Bookshelf)](https://www.ncbi.nlm.nih.gov/books/NBK10960/)
- [Physiology, Neurotransmitters — StatPearls (NCBI Bookshelf)](https://www.ncbi.nlm.nih.gov/books/NBK539894/)
- [Types of glia — Queensland Brain Institute](https://qbi.uq.edu.au/brain-basics/brain/brain-physiology/types-glia)
- [Histology, Glial Cells — StatPearls (NCBI Bookshelf)](https://www.ncbi.nlm.nih.gov/books/NBK441945/)
- [Neurons and Glial Cells: Glia — Biology LibreTexts](https://bio.libretexts.org/Bookshelves/Introductory_and_General_Biology/General_Biology_(Boundless)/35%3A_The_Nervous_System/35.03%3A_Neurons_and_Glial_Cells_-_Glia)
- [Nodes of Ranvier: structure and function — Kenhub](https://www.kenhub.com/en/library/physiology/nodes-of-ranvier)
- [Saltatory conduction: mechanism and function — Kenhub](https://www.kenhub.com/en/library/physiology/saltatory-conduction)
- [Node of Ranvier — Wikipedia](https://en.wikipedia.org/wiki/Node_of_Ranvier)
- [The Ionic Basis of the Resting Membrane Potential — Neuroscience (NCBI Bookshelf)](https://www.ncbi.nlm.nih.gov/books/NBK10931/)
- [Physiology, Resting Potential — StatPearls (NCBI Bookshelf)](https://www.ncbi.nlm.nih.gov/books/NBK538338/)
- [The Membrane at Rest — Foundations of Neuroscience (MSU)](https://openbooks.lib.msu.edu/neuroscience/chapter/the-membrane-at-rest/)
- [Physiology, Action Potential — StatPearls (NCBI Bookshelf)](https://www.ncbi.nlm.nih.gov/books/NBK538143/)
- [Neuroanatomy, Neuron Action Potential — StatPearls (NCBI Bookshelf)](https://www.ncbi.nlm.nih.gov/books/NBK546639/)
- [Action Potential — Lumen Learning, Biology for Majors II](https://courses.lumenlearning.com/wm-biology2/chapter/action-potential/)
- [Voltage-gated sodium channel — Wikipedia](https://en.wikipedia.org/wiki/Voltage-gated_sodium_channel)
- [Chemical synapse — Wikipedia](https://en.wikipedia.org/wiki/Chemical_synapse)
- [Neurotransmitter Release — Foundations of Neuroscience (MSU)](https://openbooks.lib.msu.edu/neuroscience/chapter/neurotransmitter-release/)
- [Chemical synapses: structure, function and diagram — Kenhub](https://www.kenhub.com/en/library/physiology/chemical-synapses)
- [Postsynaptic potentials: EPSPs and IPSPs — Kenhub](https://www.kenhub.com/en/library/physiology/postsynaptic-potentials)
- [Excitatory and Inhibitory Synaptic Signalling — TeachMePhysiology](https://teachmephysiology.com/nervous-system/synapses/excitatory-and-inhibitory-signalling-synapses-neurology-teachmephysiology/)
- [Brain Glucose Metabolism: Integration of Energetics with Function — Physiological Reviews](https://journals.physiology.org/doi/full/10.1152/physrev.00062.2017)
- [A Cellular Perspective on Brain Energy Metabolism and Functional Imaging — Neuron (Cell)](https://www.cell.com/neuron/fulltext/S0896-6273(15)00259-7)
