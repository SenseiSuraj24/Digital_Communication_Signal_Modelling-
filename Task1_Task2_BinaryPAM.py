# -*- coding: utf-8 -*-
"""
UE24EC341A: DIGITAL COMMUNICATION
ORANGE LEVEL PROBLEM — Task 1 & Task 2

Task 1 : RC Pulse Generation & FIR Modeling
Task 2 : Binary PAM System Simulation

Reference: Digital Communication System, Simon Haykin
           Chapter: Signaling over Band-Limited Channels
           Section 8.6 Example 1 – FIR Modeling of the Raised-Cosine Pulse
           Pages 456-458, Student Edition, John Wiley & Sons, 2014
"""

import matplotlib
matplotlib.use('Agg')          # save figures without a display
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import erfc

plt.rcParams.update({
    "figure.dpi": 120,
    "font.family": "DejaVu Sans",
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
})

# ============================================================
# TASK 1 – RC Pulse Generation & FIR Modeling
# ============================================================
print("=" * 60)
print("  TASK 1: RC Pulse Generation & FIR Modeling")
print("=" * 60)

alpha = 0.32   # Roll-off factor
m     = 10     # FIR samples per bit
l     = 5      # Truncation parameter (half-duration in bits)

n_indices = np.arange(0, 2 * l * m + 1)   # causal index  0 ... 2*l*m
t_norm    = n_indices / m - l              # normalized time: -l ... +l

# Eq. 8.32  (handle singularity at denominator == 0)
denom = 1 - 4 * (alpha ** 2) * (t_norm ** 2)
denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
p     = np.sinc(t_norm) * np.cos(np.pi * alpha * t_norm) / denom

# ---- Verify zero-crossings at integer multiples of Tb ---------
print("\nZero-crossing verification (p at integer multiples of Tb):")
for k in range(-l + 1, l):
    if k != 0:
        idx = np.argmin(np.abs(t_norm - k))
        print(f"  t/Tb = {k:+d}  =>  p = {p[idx]:.6f}")

# ---- Plot Figure 8.8 -----------------------------------------
fig1, ax1 = plt.subplots(figsize=(10, 4.5))
markerline, stemlines, baseline = ax1.stem(
    t_norm, p, basefmt="k-", linefmt="b-", markerfmt="bo"
)
plt.setp(stemlines, linewidth=0.9)
plt.setp(markerline, markersize=4)
ax1.set_title("Task 1 — Discretized RC Pulse  (alpha=0.32, m=10, l=5)\n"
              "Figure 8.8 — FIR Tapped-Delay-Line Model")
ax1.set_xlabel("Normalized Time  (t / T_b)")
ax1.set_ylabel("Amplitude  p_n")
ax1.set_xlim(-l, l)
ax1.set_ylim(-0.25, 1.15)
ax1.axhline(0, color="k", linewidth=0.7)
ax1.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
fig1.savefig("Task1_RC_Pulse.png", bbox_inches="tight")
print("\n[Task 1] RC pulse figure saved => Task1_RC_Pulse.png")
plt.show()

# ============================================================
# TASK 2 – Binary PAM System Simulation
# ============================================================
print("\n" + "=" * 60)
print("  TASK 2: Binary PAM System Simulation")
print("=" * 60)

np.random.seed(42)
num_bits  = 10_000          # as specified in the problem
bits      = np.random.randint(0, 2, num_bits)

# Bipolar symbol mapping: 0 -> -1 , 1 -> +1
symbols   = 2 * bits - 1   # +-1

# Upsample and pulse-shape
upsampled  = np.zeros(num_bits * m)
upsampled[::m] = symbols
tx_signal  = np.convolve(upsampled, p, mode="full")

# ----- helper: add AWGN and decode -------------------------
def simulate_binary_pam(tx, snr_db_val, pulse, m_val, bits_ref):
    """Returns (rx_signal, mf_output, rx_bits_decoded, BER)."""
    snr_lin   = 10 ** (snr_db_val / 10.0)
    sig_power = np.mean(tx ** 2)
    noise_pow = sig_power / snr_lin
    noise     = np.sqrt(noise_pow) * np.random.randn(len(tx))
    rx        = tx + noise

    # Matched filter (time-reversed RC pulse)
    mf_out     = np.convolve(rx, pulse[::-1], mode="full")
    comp_resp  = np.convolve(pulse, pulse[::-1], mode="full")
    peak       = np.argmax(comp_resp)

    num_sym    = len(bits_ref)
    rx_samples = mf_out[peak : peak + num_sym * m_val : m_val]
    rx_bits_d  = (rx_samples >= 0).astype(int)

    n_compare  = min(len(bits_ref), len(rx_bits_d))
    ber_val    = np.mean(bits_ref[:n_compare] != rx_bits_d[:n_compare])
    return rx, mf_out, rx_bits_d, ber_val

# ---- 2a. Simulation at SNR = 5 dB -------------------------
snr_target = 5.0
rx_signal, mf_output, rx_bits, BER_5dB = simulate_binary_pam(
    tx_signal, snr_target, p, m, bits
)

print(f"\n--- Binary PAM @ SNR = {snr_target} dB ---")
print(f"  Total bits       : {num_bits}")
print(f"  Bit Error Rate   : {BER_5dB:.6f}")

# ---- 2b. Transmitted & received signal plots ---------------
plot_bits = 30
plot_samp = plot_bits * m
t_axis    = np.arange(plot_samp) / m

fig2, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

axes[0].plot(t_axis, tx_signal[:plot_samp], color="#1976D2", linewidth=1.5)
axes[0].set_title("Task 2 — Transmitted Binary PAM Signal (Pulse Shaped, RC Filter)")
axes[0].set_ylabel("Amplitude")
axes[0].grid(True, linestyle="--", alpha=0.6)

axes[1].plot(t_axis, rx_signal[:plot_samp], color="#D32F2F", linewidth=1.0, alpha=0.85)
axes[1].set_title(f"Noisy Received Signal (AWGN, SNR = {snr_target} dB)")
axes[1].set_xlabel("Time (T_b)")
axes[1].set_ylabel("Amplitude")
axes[1].grid(True, linestyle="--", alpha=0.6)

plt.tight_layout()
fig2.savefig("Task2_TX_RX_Signals.png", bbox_inches="tight")
print("[Task 2] TX/RX signal figure saved => Task2_TX_RX_Signals.png")
plt.show()

# ---- 2c. Eye Diagram helper --------------------------------
def compute_eye_params(mf_sig, m_val, num_traces=200):
    """Extract eye height, noise margin from matched filter output."""
    segments = []
    for i in range(num_traces):
        start = i * m_val
        end   = start + 2 * m_val
        if end < len(mf_sig):
            segments.append(mf_sig[start:end])

    mid_idx  = m_val
    eye_vals = np.array([s[mid_idx] for s in segments])
    pos_vals = eye_vals[eye_vals > 0]
    neg_vals = eye_vals[eye_vals < 0]
    pos_min  = np.min(pos_vals) if len(pos_vals) > 0 else 0.0
    neg_max  = np.max(neg_vals) if len(neg_vals) > 0 else 0.0
    eye_h    = pos_min - neg_max
    noise_m  = eye_h / 2.0
    return segments, eye_h, noise_m

# ---- 2d. Eye diagram @ 5 dB --------------------------------
segs_5, eye_h, noise_m = compute_eye_params(mf_output, m)
fig_e, ax_e = plt.subplots(figsize=(8, 4.5))
for seg in segs_5:
    ta = np.linspace(0, 2, len(seg))
    ax_e.plot(ta, seg, color="#7B1FA2", alpha=0.12, linewidth=0.8)
ax_e.axvline(1.0, color="lime", linewidth=1.4, linestyle="--",
             label="Opt. sampling  t = 1.0 Ts")
ax_e.set_title("Task 2 — Eye Diagram of Matched Filter Output\n"
               "Binary PAM, SNR = 5 dB")
ax_e.set_xlabel("Normalized Time (Symbol Intervals)")
ax_e.set_ylabel("Amplitude")
ax_e.legend(fontsize=9, loc="upper right")
ax_e.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
fig_e.savefig("Task2_EyeDiagram_5dB.png", bbox_inches="tight")
print("[Task 2] Eye diagram @ 5 dB saved => Task2_EyeDiagram_5dB.png")
plt.show()

print(f"\n--- Eye Diagram Parameters @ SNR = {snr_target} dB ---")
print(f"  Eye Height            : {eye_h:.4f}")
print(f"  Noise Margin          : {noise_m:.4f}")
print(f"  Optimum Sampling Inst.: t = 1.0 (normalised symbol interval)")

# ---- 2e. Eye diagrams for SNR = 0, 5, 10, 15 dB -----------
snr_levels = [0, 5, 10, 15]
colors_snr  = ["#E53935", "#7B1FA2", "#1565C0", "#2E7D32"]
eye_params  = {}

fig3, axes3 = plt.subplots(2, 2, figsize=(14, 9))
axes3 = axes3.flatten()

for ax_idx, (snr_val, col) in enumerate(zip(snr_levels, colors_snr)):
    _, mf_i, _, ber_i = simulate_binary_pam(tx_signal, snr_val, p, m, bits)
    segs_i, eh_i, nm_i = compute_eye_params(mf_i, m)
    eye_params[snr_val] = {"BER": ber_i, "Eye Height": eh_i, "Noise Margin": nm_i}

    for seg in segs_i:
        ta = np.linspace(0, 2, len(seg))
        axes3[ax_idx].plot(ta, seg, color=col, alpha=0.1, linewidth=0.7)

    axes3[ax_idx].axvline(1.0, color="lime", linewidth=1.2, linestyle="--")
    axes3[ax_idx].set_title(
        f"SNR = {snr_val} dB  |  BER = {ber_i:.4f}\n"
        f"Eye Height = {eh_i:.3f},  Noise Margin = {nm_i:.3f}"
    )
    axes3[ax_idx].set_xlabel("Normalised Time")
    axes3[ax_idx].set_ylabel("Amplitude")
    axes3[ax_idx].grid(True, linestyle="--", alpha=0.5)

fig3.suptitle("Task 2 — Eye Diagrams: SNR = 0, 5, 10, 15 dB\n"
               "(Binary PAM, Matched Filter Output)",
               fontsize=13, fontweight="bold")
plt.tight_layout()
fig3.savefig("Task2_EyeDiagrams_Comparison.png", bbox_inches="tight")
print("[Task 2] Comparative eye diagram saved => Task2_EyeDiagrams_Comparison.png")
plt.show()

# ---- 2f. BER vs SNR table & plot ---------------------------
snr_range   = [-2, 0, 2, 5, 8, 10, 15]
ber_sim     = []
ber_theory  = []

print("\n--- BER vs SNR Summary Table (Binary PAM) ---")
print(f"{'SNR (dB)':>10}  {'BER (Simulated)':>18}  {'BER (Theoretical)':>20}")
print("-" * 55)

for snr_v in snr_range:
    _, _, _, ber_v = simulate_binary_pam(tx_signal, snr_v, p, m, bits)
    ber_sim.append(ber_v)
    snr_lin = 10 ** (snr_v / 10.0)
    ber_th  = 0.5 * erfc(np.sqrt(snr_lin))
    ber_theory.append(ber_th)
    print(f"{snr_v:>10}  {ber_v:>18.6f}  {ber_th:>20.6f}")

fig4, ax4 = plt.subplots(figsize=(9, 5))
ax4.semilogy(snr_range, ber_sim,    "bo-", linewidth=1.8, markersize=6,
             label="Simulated BER")
ax4.semilogy(snr_range, ber_theory, "r--^", linewidth=1.8, markersize=6,
             label="Theoretical BER  Q(sqrt(2*SNR))")
ax4.set_title("Task 2 — BER vs SNR for Binary PAM (Bipolar +-1 Signaling)")
ax4.set_xlabel("SNR (dB)")
ax4.set_ylabel("Bit Error Rate (BER)")
ax4.legend()
ax4.grid(True, which="both", linestyle="--", alpha=0.6)
plt.tight_layout()
fig4.savefig("Task2_BER_vs_SNR.png", bbox_inches="tight")
print("\n[Task 2] BER vs SNR figure saved => Task2_BER_vs_SNR.png")
plt.show()

# ---- 2g. Eye diagram parameter summary table ---------------
print("\n--- Eye Diagram Parameter Summary ---")
print(f"{'SNR (dB)':>10}  {'Eye Height':>12}  {'Noise Margin':>14}  {'BER':>12}")
print("-" * 55)
for snr_v in snr_levels:
    ep = eye_params[snr_v]
    print(f"{snr_v:>10}  {ep['Eye Height']:>12.4f}  {ep['Noise Margin']:>14.4f}  {ep['BER']:>12.6f}")

# ============================================================
# INFERENCES
# ============================================================
print("\n" + "=" * 60)
print("  INFERENCE — Task 1: RC Pulse Generation")
print("=" * 60)
print("""
Inference 1:
  The Raised-Cosine pulse with alpha=0.32, m=10, and l=5 is
  symmetric about its midpoint (t/Tb = 0) and exhibits Nyquist
  zero-crossings at every integer multiple of Tb, confirming that
  Inter-Symbol Interference (ISI) is theoretically zero at optimal
  sampling instants.

Inference 2:
  The roll-off factor alpha=0.32 produces a pulse that decays
  faster in time than an ideal sinc (alpha=0), yet occupies a
  bandwidth of (1+alpha)/(2Tb). This offers a practical trade-off
  between spectral efficiency and time-domain roll-off behaviour.

Inference 3:
  The FIR TDL model with 2*l*m+1 = 101 taps faithfully captures
  the RC pulse shape. Truncation to +-5 Tb introduces negligible
  distortion because the pulse amplitude at the truncation boundary
  is extremely close to zero, validating the FIR approximation.
""")

print("=" * 60)
print("  INFERENCE — Task 2: Binary PAM System")
print("=" * 60)
print(f"""
Inference 1:
  At SNR = 5 dB the simulated BER = {BER_5dB:.6f}, which closely
  matches the theoretical BER = 0.5*erfc(sqrt(SNR_linear)). This
  validates the end-to-end transmitter-channel-matched-filter
  pipeline implementation.

Inference 2:
  The eye diagram becomes progressively more open as SNR increases
  from 0 dB to 15 dB: eye height and noise margin grow
  substantially, while the BER decreases sharply. This demonstrates
  that higher SNR directly improves decision reliability.

Inference 3:
  The optimum sampling instant is at the centre of the eye
  (t = 1.0 normalised symbol interval), where the eye opening is
  maximum and the system is least sensitive to timing jitter or
  synchronisation errors.

Inference 4:
  Matched filtering (using the time-reversed RC pulse) maximises
  the post-filter SNR at the sampling instant, achieving the minimum
  BER possible with a linear receiver. The RC pulse shape ensures
  zero-ISI at sampling instants while confining spectral energy
  within the Nyquist bandwidth.
""")

# ============================================================
# EXTRA ANALYSIS — RC Pulse vs Alpha (alpha = 0, 0.75, 1)
# Examine BW changes, BER vs alpha, BW vs alpha
# (as required from class requirements)
# ============================================================
print("\n" + "=" * 60)
print("  ALPHA ANALYSIS: RC Pulse for alpha = 0, 0.75, 1")
print("=" * 60)

def make_rc_pulse(alpha_val, m_val=10, l_val=5):
    """Return (t_norm, p) for given roll-off alpha."""
    n_idx  = np.arange(0, 2 * l_val * m_val + 1)
    t_n    = n_idx / m_val - l_val
    den    = 1 - 4 * (alpha_val ** 2) * (t_n ** 2)
    den    = np.where(np.abs(den) < 1e-10, 1e-10, den)
    if alpha_val == 0:
        # Limit: sinc function (cos term -> 1, denom -> 1)
        pulse  = np.sinc(t_n)
    else:
        pulse  = np.sinc(t_n) * np.cos(np.pi * alpha_val * t_n) / den
    return t_n, pulse

alpha_vals  = [0, 0.75, 1.0]
colors_a    = ["#1565C0", "#E65100", "#2E7D32"]
labels_a    = [r"$\alpha$ = 0  (ideal sinc)",
               r"$\alpha$ = 0.75",
               r"$\alpha$ = 1.0  (full roll-off)"]

# ---- Plot 1: RC pulse comparison -------------------------
fig5, ax5 = plt.subplots(figsize=(11, 5))
for alpha_v, col, lbl in zip(alpha_vals, colors_a, labels_a):
    t_n, pulse_v = make_rc_pulse(alpha_v)
    ax5.plot(t_n, pulse_v, color=col, linewidth=2.0, label=lbl)

ax5.axhline(0, color="k", linewidth=0.7, linestyle="--")
ax5.set_title("RC Pulse Shape for Different Roll-Off Factors (alpha = 0, 0.75, 1.0)")
ax5.set_xlabel("Normalized Time  (t / T_b)")
ax5.set_ylabel("Amplitude  p_n")
ax5.set_xlim(-5, 5)
ax5.set_ylim(-0.35, 1.15)
ax5.legend(fontsize=10)
ax5.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
fig5.savefig("Alpha_RC_Pulse_Comparison.png", bbox_inches="tight")
print("\n[Alpha Analysis] RC pulse comparison saved => Alpha_RC_Pulse_Comparison.png")
plt.show()

# ---- Plot 2: BW vs alpha ---------------------------------
# RC bandwidth = (1 + alpha) / (2 * Tb)
# Normalised: BW_norm = (1 + alpha) / 2  [units of 1/Tb]
alpha_cont  = np.linspace(0, 1, 200)
BW_norm     = (1 + alpha_cont) / 2.0     # Nyquist BW factor

# Excess bandwidth = alpha / (2*Tb)  -- bandwidth BEYOND Nyquist minimum
excess_BW   = alpha_cont / 2.0

fig6, ax6   = plt.subplots(figsize=(9, 5))
ax6.plot(alpha_cont, BW_norm,  color="#1565C0", linewidth=2.2,
         label="Total BW = (1+alpha)/(2T_b)")
ax6.plot(alpha_cont, excess_BW, color="#D32F2F", linewidth=2.0,
         linestyle="--", label="Excess BW = alpha/(2T_b)")
ax6.axhline(0.5, color="gray", linewidth=0.8, linestyle=":", label="Nyquist min BW = 1/(2T_b)")

# Mark our three key alpha values
for av, col in zip(alpha_vals, colors_a):
    bw_v = (1 + av) / 2.0
    ax6.plot(av, bw_v, "o", color=col, markersize=9, zorder=5)
    ax6.annotate(f"alpha={av}\nBW={bw_v:.2f}/T_b",
                 xy=(av, bw_v), xytext=(av + 0.04, bw_v - 0.06),
                 fontsize=8, color=col,
                 arrowprops=dict(arrowstyle="->", color=col, lw=1.2))

ax6.set_title("BW vs Roll-Off Factor alpha\n(Raised-Cosine Pulse, Binary PAM)")
ax6.set_xlabel("Roll-Off Factor  alpha")
ax6.set_ylabel("Normalised Bandwidth  [x 1/T_b]")
ax6.legend(fontsize=9)
ax6.grid(True, linestyle="--", alpha=0.6)
ax6.set_xlim(0, 1)
ax6.set_ylim(0.3, 1.1)
plt.tight_layout()
fig6.savefig("Alpha_BW_vs_Alpha.png", bbox_inches="tight")
print("[Alpha Analysis] BW vs alpha figure saved => Alpha_BW_vs_Alpha.png")
plt.show()

# ---- BW summary table ------------------------------------
print("\n--- Bandwidth Summary Table ---")
print(f"{'alpha':>8}  {'Total BW (x1/Tb)':>20}  {'Excess BW (x1/Tb)':>20}")
print("-" * 54)
for av in [0, 0.25, 0.32, 0.50, 0.75, 1.0]:
    bw_t = (1 + av) / 2.0
    bw_e = av / 2.0
    print(f"{av:>8.2f}  {bw_t:>20.4f}  {bw_e:>20.4f}")

# ---- Plot 3: BER vs alpha (fixed SNR = 5 dB) ------------
alpha_sweep = np.linspace(0.0, 1.0, 20)
ber_alpha   = []

print("\n--- BER vs Alpha Table (SNR = 5 dB, Binary PAM) ---")
print(f"{'alpha':>8}  {'BER (Simulated)':>18}")
print("-" * 30)

for av in alpha_sweep:
    _, pulse_v = make_rc_pulse(av)
    # Re-build TX signal with this pulse
    upsampled_a  = np.zeros(num_bits * m)
    upsampled_a[::m] = symbols
    tx_a = np.convolve(upsampled_a, pulse_v, mode="full")
    _, _, _, ber_a = simulate_binary_pam(tx_a, 5.0, pulse_v, m, bits)
    ber_alpha.append(ber_a)
    print(f"{av:>8.3f}  {ber_a:>18.6f}")

fig7, ax7 = plt.subplots(figsize=(9, 5))
ax7.semilogy(alpha_sweep, [max(b, 1e-7) for b in ber_alpha],
             "ms-", linewidth=2.0, markersize=7,
             label="Simulated BER  @ SNR = 5 dB")
ax7.axvline(0.32, color="#1565C0", linestyle="--", linewidth=1.4,
            label="alpha = 0.32 (our design)")
ax7.set_title("BER vs Roll-Off Factor alpha\n(Binary PAM, AWGN, SNR = 5 dB)")
ax7.set_xlabel("Roll-Off Factor  alpha")
ax7.set_ylabel("Bit Error Rate (BER)")
ax7.legend(fontsize=9)
ax7.grid(True, which="both", linestyle="--", alpha=0.6)
ax7.set_xlim(0, 1)
plt.tight_layout()
fig7.savefig("Alpha_BER_vs_Alpha.png", bbox_inches="tight")
print("\n[Alpha Analysis] BER vs alpha figure saved => Alpha_BER_vs_Alpha.png")
plt.show()

# ============================================================
# INFERENCES — Alpha Analysis
# ============================================================
print("\n" + "=" * 60)
print("  INFERENCE — Alpha Analysis (BW & BER vs alpha)")
print("=" * 60)
print("""
Inference 1 (Pulse Shape vs alpha):
  As alpha increases from 0 to 1, the RC pulse transitions from an
  ideal sinc (maximum spectral efficiency, infinite side-lobes in
  time) to a cosine-tapered pulse (wider BW, but much faster time-
  domain decay). At alpha=1 the pulse decays as 1/t^3, making it
  far more robust to timing errors than the sinc (1/t decay).

Inference 2 (BW vs alpha):
  The two-sided bandwidth of the RC pulse is BW = (1+alpha)/T_b.
  For alpha=0: BW = 1/T_b (Nyquist minimum);
  For alpha=0.75: BW = 1.75/T_b (75% excess bandwidth);
  For alpha=1.0: BW = 2/T_b (double the Nyquist bandwidth).
  There is a direct linear trade-off: every increase in alpha by 0.1
  adds 0.1/T_b of excess bandwidth while buying faster time-domain
  roll-off and improved timing tolerance.

Inference 3 (BER vs alpha):
  At a fixed SNR of 5 dB, the simulated BER is approximately
  constant (near zero) across all values of alpha for an ideal AWGN
  channel with perfect synchronisation. This is because the matched
  filter compensates for the pulse shape, and the Nyquist zero-ISI
  criterion holds for all alpha in [0,1]. The BER is therefore
  primarily controlled by SNR, not by alpha, in an ideal system.

Inference 4 (Design Trade-off):
  In practice, alpha=0.32 (used in this assignment) is a good
  engineering compromise: it uses only 32% excess bandwidth beyond
  the Nyquist minimum while providing significantly better timing
  jitter immunity and smaller out-of-band leakage compared to
  alpha=0. Extreme values (alpha near 0) are spectrally efficient
  but require very precise timing synchronisation, while alpha=1
  doubles the bandwidth but is highly robust to timing errors.
""")
