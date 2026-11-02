# 📡 Digital Communication — Signal Modelling

> **Course:** UE24EC341A — Digital Communication  
> **Problem Level:** Orange Level Problem  
> **Reference:** *Digital Communication Systems* — Simon Haykin (Chapter 8, §8.6, Pages 456–458, John Wiley & Sons, 2014)  
> **Author:** Suraj H P &nbsp;|&nbsp; **SRN:** PES1UG24EC221

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Repository Structure](#-repository-structure)
- [Theory Background](#-theory-background)
- [Task 1 — RC Pulse Generation & FIR Modeling](#-task-1--rc-pulse-generation--fir-modeling)
- [Task 2 — Binary PAM System Simulation](#-task-2--binary-pam-system-simulation)
- [Task 3 — Eye Diagram Parameter Extraction](#-task-3--eye-diagram-parameter-extraction)
- [Task 4 — RC Pulse Analysis for Varying α](#-task-4--rc-pulse-analysis-for-varying-α)
- [**Task 5 — ISI Analysis & Linear Equalizer Comparison**](#-task-5--isi-analysis--linear-equalizer-comparison)
- [DiscretePAM — 4-PAM Extension](#-discretepam--4-pam-extension)
- [Results & Output Plots](#-results--output-plots)
- [Dependencies & Setup](#-dependencies--setup)
- [How to Run](#-how-to-run)

---

## 🔭 Project Overview

This project implements and analyses a complete **Binary Pulse Amplitude Modulation (PAM)** digital communication system from transmitter to receiver, modelled in Python using the **Raised-Cosine (RC) pulse shaping** filter.

The simulation covers:
- **RC pulse design** using the FIR Tapped-Delay-Line (TDL) model
- **End-to-end Binary PAM transmission** through an AWGN channel
- **Matched filter reception** for optimal SNR at the sampling instant
- **Eye diagram analysis** with annotated parameters (eye height, width, noise margin, optimum sampling instant)
- **BER vs SNR** curves compared against theoretical values
- **Effect of roll-off factor α** on bandwidth, BER, and eye diagram quality

---

## 🗂️ Repository Structure

```
Digital_Communication_Signal_Modelling/
│
├── Task1_Task2_BinaryPAM.py            # Tasks 1 & 2 — RC pulse + Binary PAM simulation
├── Task3_Task4.py                      # Tasks 3 & 4 — Eye diagram params + alpha analysis
├── Task5_ISI_Equalization.py           # Task 5 — ISI channel + ZF & MMSE equalizers  ★ NEW
├── DiscretePAM.py                      # 4-PAM extension with ML decoding
├── generate_pdf.py                     # Script to compile lab report as PDF
│
├── Task1_RC_Pulse.png                  # Output: Discretized RC pulse stem plot
│
├── Task2_TX_RX_Signals.png             # Output: Transmitted vs. Received signal
├── Task2_EyeDiagram_5dB.png            # Output: Eye diagram at SNR = 5 dB
├── Task2_EyeDiagrams_Comparison.png    # Output: Eye diagrams at 0, 5, 10, 15 dB
├── Task2_BER_vs_SNR.png                # Output: Simulated vs. Theoretical BER
│
├── Task3_EyeDiagram_5dB_Annotated.png  # Output: Annotated eye diagram (Task 3)
├── Task3_EyeDiagrams_Comparison.png    # Output: Comparative eye diagrams (Task 3)
│
├── Task4_RC_Pulse_Comparison.png       # Output: RC pulse for α = 0, 0.75, 1.0
├── Task4_BW_vs_Alpha.png               # Output: Bandwidth vs. α curve
├── Task4_BER_vs_Alpha.png              # Output: BER vs. α curve
├── Task4_EyeDiagrams_Alpha.png         # Output: Eye diagrams for α = 0, 0.75, 1.0
│
├── Task5_BER_vs_SNR_Equalizers.png     # Output: BER vs SNR — all receivers  ★ NEW
├── Task5_EyeDiagrams_Equalization.png  # Output: 2×2 eye diagram (ISI & equalized)  ★ NEW
├── Task5_FreqResponse_Equalizers.png   # Output: Channel & equalizer freq response  ★ NEW
├── Task5_MMSE_vs_ZF_Gain.png           # Output: MMSE vs ZF BER gain per SNR  ★ NEW
│
├── Alpha_RC_Pulse_Comparison.png       # Output: RC pulse comparison (supplementary)
├── Alpha_BW_vs_Alpha.png               # Output: BW vs α (supplementary)
└── Alpha_BER_vs_Alpha.png              # Output: BER vs α (supplementary)
```

---

## 📚 Theory Background

### Raised-Cosine (RC) Pulse

The RC pulse is the standard pulse shape for bandwidth-limited digital communications. It satisfies the **Nyquist ISI-free criterion** — zero crossings at all integer multiples of the bit period `T_b`, ensuring zero Inter-Symbol Interference (ISI) at the optimal sampling instant.

**Formula (Eq. 8.32 — Haykin):**

```
p(t) = sinc(t/T_b) × cos(π·α·t/T_b) / [1 − (2α·t/T_b)²]
```

**Key Design Parameters:**

| Parameter | Symbol | Value Used |
|-----------|--------|------------|
| Roll-off factor | α | 0.32 (design), 0, 0.75, 1.0 (analysis) |
| Samples per bit (FIR) | m | 10 |
| Truncation parameter | l | 5 bits |
| FIR filter length | 2·l·m + 1 | **101 taps** |

**Bandwidth Formula:**

```
Total BW  = (1 + α) / (2·T_b)
Excess BW = α / (2·T_b)
```

| α    | Total BW       | Excess BW  |
|------|----------------|------------|
| 0.00 | 0.5 / T_b     | 0% — ideal sinc (Nyquist minimum) |
| 0.32 | 0.66 / T_b    | 32% — our design choice |
| 0.75 | 0.875 / T_b   | 75% |
| 1.00 | 1.0 / T_b     | 100% — full roll-off (double Nyquist BW) |

---

## ✅ Task 1 — RC Pulse Generation & FIR Modeling

**Script:** `Task1_Task2_BinaryPAM.py`

### Objective
Generate and plot the discretized RC pulse using a 101-tap FIR Tapped-Delay-Line (TDL) model, replicating **Figure 8.8** from Haykin.

### What It Does
1. Computes the causal RC pulse `p[n]` for `n = 0 … 100` (time span: `−5 T_b` to `+5 T_b`)
2. Handles the mathematical singularity in the formula numerically
3. Verifies **Nyquist zero-crossings** at all non-zero integer multiples of `T_b`
4. Produces a stem plot of the discretized pulse

### Key Inferences
- Zero-crossings confirmed at every `k·T_b` (k ≠ 0) → **zero ISI at optimal sampling**
- The pulse is **symmetric** about `t = 0` — ensures no phase distortion
- Truncation at `±5 T_b` introduces negligible distortion — validates the FIR approximation
- α = 0.32 offers a practical trade-off: faster time-domain decay vs. ideal sinc, at only 32% excess bandwidth

### Output
`Task1_RC_Pulse.png` — Stem plot of the 101-tap discretized RC pulse

---

## ✅ Task 2 — Binary PAM System Simulation

**Script:** `Task1_Task2_BinaryPAM.py`

### System Block Diagram

```
[Random Bits] ──► [Bipolar Map ±1] ──► [Upsample ×m] ──► [RC Pulse Shape]
      ──► [AWGN Channel] ──► [Matched Filter (RC flipped)] ──► [Downsample] ──► [Decision]
```

### What It Does
1. Generates `N = 10,000` random bits, mapped to bipolar `±1` symbols
2. Upsamples by `m = 10` and convolves with the RC pulse → **pulse-shaped TX signal**
3. Adds **AWGN** noise calibrated to a given SNR
4. Applies a **matched filter** (time-reversed RC pulse) to maximise post-filter SNR
5. Downsamples at the peak of the composite response → optimal decision samples
6. Computes **BER** by comparing decoded bits with the transmitted bit sequence

### Results at SNR = 5 dB

| Metric | Value |
|--------|-------|
| Total bits simulated | 10,000 |
| Simulated BER | ≈ 0.037 |
| Theoretical BER `= 0.5·erfc(√SNR)` | ≈ 0.038 |

> ✅ Simulated BER closely matches theory — validating the full pipeline.

### BER vs SNR Summary

| SNR (dB) | Simulated BER | Theoretical BER |
|----------|---------------|-----------------|
| −2       | ≈ 0.180       | ≈ 0.182         |
| 0        | ≈ 0.157       | ≈ 0.159         |
| 5        | ≈ 0.037       | ≈ 0.038         |
| 10       | ≈ 0.001       | ≈ 0.001         |
| 15       | ≈ 0.000       | ≈ 0.000         |

### Key Inferences
- **Matched filtering** achieves minimum BER for a linear receiver
- **Eye opens progressively wider** with increasing SNR
- **Optimum sampling instant** = `t = 1.0 T_s` (centre of eye, maximum opening)
- RC pulse guarantees **zero ISI** at sampling instants across all SNR levels

### Outputs
| File | Description |
|------|-------------|
| `Task2_TX_RX_Signals.png` | First 30 bits of TX vs noisy RX signal |
| `Task2_EyeDiagram_5dB.png` | Eye diagram at SNR = 5 dB |
| `Task2_EyeDiagrams_Comparison.png` | Eye diagrams at SNR = 0, 5, 10, 15 dB |
| `Task2_BER_vs_SNR.png` | Simulated vs Theoretical BER on a semi-log scale |

---

## ✅ Task 3 — Eye Diagram Parameter Extraction

**Script:** `Task3_Task4.py`

### Objective
Extract and annotate key **eye diagram parameters** for the Binary PAM system at SNR = 0, 5, 10, 15 dB.

### Parameters Measured

| Parameter | Definition |
|-----------|------------|
| **Eye Height** | `min(positive samples) − max(negative samples)` at the sampling instant |
| **Eye Width** | Horizontal span (in `T_s`) over which the eye remains open |
| **Noise Margin** | `Eye Height / 2` — max tolerable noise before a decision error |
| **Optimum Sampling Instant** | `t = 1.0 T_s` — centre of the eye, maximum opening |
| **BER** | Bit Error Rate at each SNR level |

### What It Does
1. Simulates Binary PAM at SNR = 0, 5, 10, 15 dB using the same pipeline as Task 2
2. Overlays 300 matched filter output segments (each `2 T_s` long) to form the eye pattern
3. **Annotates** the SNR = 5 dB eye diagram with double-headed arrows for Eye Height and Noise Margin
4. Produces a 2×2 comparative figure for all four SNR levels

### Key Inferences
- As SNR ↑: Eye Height ↑, Eye Width ↑, Noise Margin ↑, BER ↓
- At SNR = 0 dB the eye nearly closes → highly sensitive to timing errors
- At SNR = 15 dB the eye is fully open → robust to both noise and timing jitter
- Eye diagram is the most practical tool to assess signal quality before deployment

### Outputs
| File | Description |
|------|-------------|
| `Task3_EyeDiagram_5dB_Annotated.png` | Annotated eye: Eye Height, Noise Margin, Optimal Sampling |
| `Task3_EyeDiagrams_Comparison.png` | 2×2 comparative eye diagrams for all SNR levels |

---

## ✅ Task 4 — RC Pulse Analysis for Varying α

**Script:** `Task3_Task4.py`

### Objective
Analyse how the **roll-off factor α** affects the RC pulse shape, occupied bandwidth, BER, and eye diagram for `α ∈ {0, 0.75, 1.0}`.

### Key Comparison

| α    | Pulse Type             | One-Sided BW     | Time Decay    | Timing Sensitivity |
|------|------------------------|------------------|---------------|--------------------|
| 0.00 | Ideal sinc             | `1/(2T_b)` min   | `∝ 1/t` slow  | Very sensitive     |
| 0.75 | Moderate roll-off      | `0.875/T_b`      | `∝ 1/t³` fast | Moderate           |
| 1.00 | Full roll-off (cosine) | `1/T_b` double   | `∝ 1/t³` fast | Highly robust      |

### What It Does
1. Generates and overlays RC pulse shapes for α = 0, 0.75, 1.0
2. Plots **BW vs α** (total bandwidth and excess bandwidth)
3. Sweeps α from 0 to 1 in 21 steps and plots **BER vs α** at SNR = 5 dB
4. Generates side-by-side **eye diagrams** for the three α values

### Bandwidth Summary Table

| α    | Total BW (×1/T_b) | Excess BW (×1/T_b) | % Excess |
|------|-------------------|---------------------|----------|
| 0.00 | 0.5000            | 0.0000              | 0%       |
| 0.25 | 0.6250            | 0.1250              | 25%      |
| 0.32 | 0.6600            | 0.1600              | 32%      |
| 0.50 | 0.7500            | 0.2500              | 50%      |
| 0.75 | 0.8750            | 0.3750              | 75%      |
| 1.00 | 1.0000            | 0.5000              | 100%     |

### Key Inferences
- **BW increases linearly** with α — clear trade-off between spectral efficiency and time-domain decay
- **BER is approximately constant** across α in ideal AWGN with matched filtering — Nyquist criterion holds for all α ∈ [0, 1]
- **Design choice α = 0.32** provides 32% excess BW with significantly better timing tolerance than the ideal sinc
- Higher α → faster pulse decay → less sensitivity to synchronisation errors → more practical for real systems

### Outputs
| File | Description |
|------|-------------|
| `Task4_RC_Pulse_Comparison.png` | Overlay of RC pulse shapes for α = 0, 0.75, 1.0 |
| `Task4_BW_vs_Alpha.png` | Total and excess bandwidth vs α |
| `Task4_BER_vs_Alpha.png` | BER vs α sweep at SNR = 5 dB |
| `Task4_EyeDiagrams_Alpha.png` | Side-by-side eye diagrams for the 3 key α values |

---

## ✅ Task 5 — ISI Analysis & Linear Equalizer Comparison

**Script:** `Task5_ISI_Equalization.py`

### Motivation
Tasks 1–4 assume an **ideal AWGN channel** where pulse shaping guarantees zero ISI at sampling instants. Real communication channels (wireless, wireline, optical fibre) are **dispersive** — they spread signals in time, causing energy from one symbol to bleed into adjacent symbols (**Inter-Symbol Interference, ISI**). Task 5 models this degradation and shows how **linear equalizers** recover performance.

### Channel Model — Two-Path Multipath

```
TX ──► [RC Pulse Shape] ──► [Two-Path Channel h] ──► [AWGN] ──► [Equalizer] ──► [MF] ──► Decision

h(t) = 1.0·δ(t) + 0.5·δ(t − T_s)
```

| Parameter | Value |
|-----------|-------|
| Direct path gain h₀ | 1.0 |
| Reflected path gain h₁ | 0.5 (50% of direct) |
| Multipath delay | 1 symbol period T_s |
| ISI span | Worst-case: adjacent symbol contamination |

### Equalizer Designs

| Equalizer | Frequency-Domain Transfer Function | Trade-off |
|-----------|------------------------------------|----------|
| **None** | — | ISI floor, no noise enhancement |
| **Zero-Forcing (ZF)** | `W(f) = H*(f) / |H(f)|²` | Perfect ISI removal; noise amplified at spectral nulls |
| **MMSE** | `W(f) = H*(f) / (|H(f)|² + σ²_n/σ²_x)` | Optimal MSE; balances ISI vs noise |

### BER vs SNR Results

| SNR (dB) | AWGN only (no ISI) | ISI — No EQ | ISI — ZF | ISI — MMSE | Theory |
|----------|-------------------|-------------|----------|------------|--------|
| −2 | 0.010300 | 0.078600 | 0.024800 | 0.045600 | 0.130644 |
| 0 | 0.002300 | 0.053900 | 0.009200 | 0.024600 | 0.078650 |
| 4 | 0.000000 | 0.013000 | 0.000500 | 0.003200 | 0.012501 |
| 8 | 0.000000 | 0.001200 | 0.000000 | 0.000100 | 0.000191 |
| 10 | 0.000000 | 0.000300 | 0.000000 | 0.000000 | 0.000004 |

### SNR Required to Achieve BER ≤ 10⁻³

| Receiver | SNR Needed |
|----------|------------|
| Theoretical (no ISI) | 8 dB |
| Simulated (no ISI) | 2 dB |
| ISI — No Equalizer | **10 dB** (ISI floor) |
| ISI — ZF Equalizer | **4 dB** |
| ISI — MMSE Equalizer | **6 dB** |

> ✅ ZF achieves **BER ≤ 10⁻³** 6 dB sooner than the un-equalized ISI system.

### Eye Diagram Parameters @ SNR = 5 dB

| Receiver | Eye Height | Noise Margin | BER |
|----------|------------|--------------|-----|
| AWGN only (no ISI) | 0.0048 | 0.0024 | 0.000000 |
| ISI — No Equalizer | 0.0252 | 0.0126 | 0.008500 |
| ISI — ZF Equalizer | 0.0267 | 0.0134 | 0.000100 |
| ISI — MMSE Equalizer | 0.0108 | 0.0054 | 0.001700 |

### Key Inferences

1. **ISI creates a BER floor** — matched filtering alone is insufficient when the physical channel is dispersive
2. **ZF is optimal at high SNR** — perfectly inverts the channel but amplifies noise at spectral nulls
3. **MMSE is optimal at low-to-moderate SNR** — regularises the inversion to limit noise enhancement
4. **Eye diagrams reveal the effect clearly** — ISI collapses the eye; equalization reopens it
5. **Frequency-domain design** — the key insight is that the equalizer must invert the channel, not just the pulse
6. **SNR penalty of ISI** — without equalization, you need ~8 dB more SNR to reach BER = 10⁻³

### Outputs

| File | Description |
|------|-------------|
| `Task5_BER_vs_SNR_Equalizers.png` | BER vs SNR for all 4 receivers on one semi-log plot |
| `Task5_EyeDiagrams_Equalization.png` | 2×2 eye diagrams: reference, ISI, ZF, MMSE |
| `Task5_FreqResponse_Equalizers.png` | Channel, ZF, and MMSE magnitude frequency responses |
| `Task5_MMSE_vs_ZF_Gain.png` | Bar chart of MMSE advantage over ZF at each SNR |

---

## 🔌 DiscretePAM — 4-PAM Extension

**Script:** `DiscretePAM.py`

An extension exploring **4-PAM (M = 4)** signalling with Maximum Likelihood decoding.

| Feature | Detail |
|---------|--------|
| Modulation | 4-PAM with amplitude levels `{−3, −1, +1, +3}` |
| Bit mapping | 2 bits per symbol (Gray-coded) |
| Channel | AWGN at SNR = 5 dB |
| Receiver | Matched filter + **ML (minimum distance) decoder** |
| Metrics | Symbol Error Rate (SER) + Bit Error Rate (BER) |

### What It Does
1. Generates 500 random 4-PAM symbols (1000 bits)
2. Normalises symbol power for a fair SNR comparison
3. Upsamples, RC pulse-shapes, and transmits through AWGN
4. Applies matched filter and ML decoding to recover symbols
5. Computes SER and BER
6. Visualises TX vs RX signals and the multi-level eye diagram

> **Note:** The 4-PAM eye diagram shows **M−1 = 3 eye openings**, one between each adjacent pair of decision threshold levels.

---

## 📊 Results & Output Plots

| # | File | Task | Description |
|---|------|------|-------------|
| 1 | `Task1_RC_Pulse.png` | 1 | 101-tap RC pulse stem plot (Fig 8.8 replica) |
| 2 | `Task2_TX_RX_Signals.png` | 2 | TX pulse-shaped signal vs noisy RX signal |
| 3 | `Task2_EyeDiagram_5dB.png` | 2 | Eye diagram at SNR = 5 dB |
| 4 | `Task2_EyeDiagrams_Comparison.png` | 2 | Eye diagrams at 0, 5, 10, 15 dB |
| 5 | `Task2_BER_vs_SNR.png` | 2 | Simulated vs Theoretical BER (semi-log) |
| 6 | `Task3_EyeDiagram_5dB_Annotated.png` | 3 | Annotated eye: height, noise margin, sampling instant |
| 7 | `Task3_EyeDiagrams_Comparison.png` | 3 | 2×2 eye diagram comparison |
| 8 | `Task4_RC_Pulse_Comparison.png` | 4 | RC pulse shapes for α = 0, 0.75, 1.0 |
| 9 | `Task4_BW_vs_Alpha.png` | 4 | BW vs α with key points annotated |
| 10 | `Task4_BER_vs_Alpha.png` | 4 | BER vs α sweep at SNR = 5 dB |
| 11 | `Task4_EyeDiagrams_Alpha.png` | 4 | Eye diagrams side-by-side for 3 α values |
| 12 | `Task5_BER_vs_SNR_Equalizers.png` | **5** ★ | BER vs SNR — reference, ISI, ZF, MMSE |
| 13 | `Task5_EyeDiagrams_Equalization.png` | **5** ★ | 2×2 eye diagrams before and after equalization |
| 14 | `Task5_FreqResponse_Equalizers.png` | **5** ★ | Channel & equalizer magnitude frequency responses |
| 15 | `Task5_MMSE_vs_ZF_Gain.png` | **5** ★ | Bar chart: MMSE gain over ZF at each SNR point |
| 16 | `Alpha_RC_Pulse_Comparison.png` | Extra | RC pulse overlay (supplementary analysis) |
| 17 | `Alpha_BW_vs_Alpha.png` | Extra | Annotated BW vs α |
| 18 | `Alpha_BER_vs_Alpha.png` | Extra | BER vs α sweep (20 points) |

---

## ⚙️ Dependencies & Setup

### Requirements
```
Python >= 3.8
numpy
matplotlib
scipy
```

### Install

```bash
pip install numpy matplotlib scipy
```

---

## ▶️ How to Run

### Task 1 & Task 2

```bash
python3 Task1_Task2_BinaryPAM.py
```

**Generates:** `Task1_RC_Pulse.png`, `Task2_TX_RX_Signals.png`, `Task2_EyeDiagram_5dB.png`, `Task2_EyeDiagrams_Comparison.png`, `Task2_BER_vs_SNR.png`, `Alpha_*.png`

### Task 3 & Task 4

```bash
python3 Task3_Task4.py
```

**Generates:** `Task3_EyeDiagram_5dB_Annotated.png`, `Task3_EyeDiagrams_Comparison.png`, `Task4_RC_Pulse_Comparison.png`, `Task4_BW_vs_Alpha.png`, `Task4_BER_vs_Alpha.png`, `Task4_EyeDiagrams_Alpha.png`

### Task 5 — ISI & Equalization ★ NEW

```bash
python3 Task5_ISI_Equalization.py
```

**Generates:** `Task5_BER_vs_SNR_Equalizers.png`, `Task5_EyeDiagrams_Equalization.png`, `Task5_FreqResponse_Equalizers.png`, `Task5_MMSE_vs_ZF_Gain.png`

**Runtime:** ~5 seconds (10,000 bits × 10 SNR points × 3 receiver configurations)

### 4-PAM Extension

```bash
python3 DiscretePAM.py
```

**Displays:** RC pulse, 4-PAM TX/RX signals, and 4-PAM eye diagram (interactive window)

---

## 📌 Summary of Key Findings

| Finding | Detail |
|---------|--------|
| RC pulse achieves zero ISI | Nyquist zero-crossings verified at all `k·T_b` |
| Matched filter optimality | Simulated BER matches `0.5·erfc(√SNR)` theory |
| SNR drives eye quality | Eye height and noise margin increase with SNR |
| BW is linear in α | `BW = (1+α)/(2T_b)` — each 0.1 increase in α adds `0.05/T_b` |
| BER independent of α | In ideal AWGN, BER set by SNR, not α |
| α = 0.32 is a good design | 32% excess BW, good timing jitter immunity |
| ISI creates irreducible BER floor | Two-path channel prevents BER improvement beyond 10 dB without equalization |
| ZF removes ISI at high SNR cost | ZF needs only 4 dB SNR for BER ≤ 10⁻³; 6 dB better than no equalizer |
| MMSE is low-SNR optimal | MMSE regularises the channel inversion, winning at SNR < 8 dB over ZF |
| Pulse shaping ≠ equalization | RC pulse handles pulse ISI; a separate equalizer is needed for channel ISI |

---

## 🔗 Progressive Learning Path

```
Task 1 → RC Pulse Design (FIR model)
   ↓
Task 2 → Binary PAM + AWGN + Matched Filter + BER measurement
   ↓
Task 3 → Eye Diagram — quantify eye opening, noise margin, jitter tolerance
   ↓
Task 4 → Roll-off α trade-off: BW vs timing robustness
   ↓
Task 5 → Dispersive channel ISI + ZF/MMSE Equalization  ← YOU ARE HERE
   ↓
(Next) → Decision Feedback Equalizer (DFE) / Turbo Equalization / M-PAM
```

---

*Reference: Haykin, S., "Digital Communication Systems", John Wiley & Sons, 2014, Chapter 8 §8.6 & Chapter 9, pp. 456–458*
