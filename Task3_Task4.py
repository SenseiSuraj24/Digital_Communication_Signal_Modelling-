# -*- coding: utf-8 -*-
"""
UE24EC341A: DIGITAL COMMUNICATION
ORANGE LEVEL PROBLEM — Task 3 & Task 4

Task 3 : Eye Diagram Parameter Extraction
          (a) Eye Height & Width
          (b) Optimum Sampling Instant
          (c) Noise Margin
          (d) Comparative Eye Diagrams at SNR = 0, 5, 10, 15 dB

Task 4 : RC Pulse for alpha = 0, 0.75, 1.0
          - Examine how Bandwidth changes with alpha
          - BER vs alpha
          - BW vs alpha

Reference: Digital Communication System, Simon Haykin
           Chapter: Signaling over Band-Limited Channels
           Section 8.6, Pages 456-458, Student Edition, John Wiley & Sons, 2014

Name  : Suraj H P
SRN   : PES1UG24EC221
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import erfc

plt.rcParams.update({
    "figure.dpi": 150,
    "font.family": "DejaVu Sans",
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ─────────────────────────────────────────────────────────────
# Shared RC pulse (alpha=0.32, m=10, l=5) — identical to Tasks 1 & 2
# ─────────────────────────────────────────────────────────────
alpha_design = 0.32
m = 10
l = 5

n_indices = np.arange(0, 2*l*m + 1)
t_norm    = n_indices / m - l
denom     = 1 - 4*(alpha_design**2)*(t_norm**2)
denom     = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
p         = np.sinc(t_norm) * np.cos(np.pi*alpha_design*t_norm) / denom

# ─────────────────────────────────────────────────────────────
# Shared Binary PAM signal
# ─────────────────────────────────────────────────────────────
np.random.seed(42)
num_bits  = 10_000
bits      = np.random.randint(0, 2, num_bits)
symbols   = 2*bits - 1

upsampled       = np.zeros(num_bits*m)
upsampled[::m]  = symbols
tx_signal       = np.convolve(upsampled, p, mode="full")


def simulate_binary_pam(tx, snr_db_val, pulse, m_val, bits_ref):
    snr_lin   = 10**(snr_db_val/10.0)
    sig_power = np.mean(tx**2)
    noise_pow = sig_power / snr_lin
    noise     = np.sqrt(noise_pow) * np.random.randn(len(tx))
    rx        = tx + noise
    mf_out    = np.convolve(rx, pulse[::-1], mode="full")
    comp_resp = np.convolve(pulse, pulse[::-1], mode="full")
    peak      = np.argmax(comp_resp)
    num_sym   = len(bits_ref)
    rx_samp   = mf_out[peak : peak + num_sym*m_val : m_val]
    rx_bits_d = (rx_samp >= 0).astype(int)
    n_cmp     = min(len(bits_ref), len(rx_bits_d))
    ber_val   = np.mean(bits_ref[:n_cmp] != rx_bits_d[:n_cmp])
    return rx, mf_out, rx_bits_d, ber_val


def extract_eye_params(mf_sig, m_val, num_traces=300):
    segments = []
    for i in range(num_traces):
        start = i * m_val
        end   = start + 2*m_val
        if end < len(mf_sig):
            segments.append(mf_sig[start:end])
    if not segments:
        return segments, 0.0, 0.0, 0.0, 1.0

    seg_arr  = np.array(segments)
    mid_idx  = m_val

    eye_vals = seg_arr[:, mid_idx]
    pos_vals = eye_vals[eye_vals > 0]
    neg_vals = eye_vals[eye_vals < 0]
    pos_min  = np.min(pos_vals) if len(pos_vals) > 0 else 0.0
    neg_max  = np.max(neg_vals) if len(neg_vals) > 0 else 0.0
    eye_h    = pos_min - neg_max
    noise_m  = eye_h / 2.0

    # Eye width: count contiguous open samples around centre
    eye_open = np.zeros(2*m_val, dtype=bool)
    for k in range(2*m_val):
        col   = seg_arr[:, k]
        p_min = np.min(col[col > 0]) if np.any(col > 0) else 0.0
        n_max = np.max(col[col < 0]) if np.any(col < 0) else 0.0
        eye_open[k] = (p_min > 0) and (n_max < 0) and (p_min > n_max)

    open_idx = np.where(eye_open)[0]
    eye_w    = (open_idx[-1] - open_idx[0]) / m_val if len(open_idx) > 1 else 0.0

    return segments, eye_h, eye_w, noise_m, 1.0


# ╔══════════════════════════════════════════════════════════════╗
# ║                     TASK  3                                  ║
# ║        Eye Diagram Parameter Extraction                      ║
# ╚══════════════════════════════════════════════════════════════╝
print("="*65)
print("  TASK 3: Eye Diagram Parameter Extraction")
print("="*65)

SNR_LEVELS = [0, 5, 10, 15]
EYE_COLORS = ["#E53935", "#7B1FA2", "#1565C0", "#2E7D32"]
eye_data   = {}

print(f"\n{'SNR (dB)':>10}  {'Eye Height':>12}  {'Eye Width (Ts)':>15}  "
      f"{'Noise Margin':>14}  {'BER':>12}")
print("-"*70)

for snr_v in SNR_LEVELS:
    _, mf_i, _, ber_i = simulate_binary_pam(tx_signal, snr_v, p, m, bits)
    segs_i, eh_i, ew_i, nm_i, oi = extract_eye_params(mf_i, m)
    eye_data[snr_v] = dict(mf=mf_i, segs=segs_i, BER=ber_i,
                           EyeHeight=eh_i, EyeWidth=ew_i,
                           NoiseMargin=nm_i, OptInstant=oi)
    print(f"{snr_v:>10}  {eh_i:>12.4f}  {ew_i:>15.4f}  {nm_i:>14.4f}  {ber_i:>12.6f}")

# ── Figure 3a: Annotated Eye Diagram @ SNR = 5 dB ───────────
d5  = eye_data[5]
eh5 = d5["EyeHeight"]
nm5 = d5["NoiseMargin"]

fig3a, ax3a = plt.subplots(figsize=(9, 5))
for seg in d5["segs"]:
    ta = np.linspace(0, 2, len(seg))
    ax3a.plot(ta, seg, color="#7B1FA2", alpha=0.10, linewidth=0.7)

ax3a.axvline(1.0, color="#00BCD4", linewidth=1.8, linestyle="--",
             label="Opt. Sampling Instant  t = 1.0 Ts")
ax3a.axhline(0, color="k", linewidth=0.6, linestyle=":")

# Double-headed arrow for eye height
ax3a.annotate("", xy=(1.0, nm5), xytext=(1.0, -nm5),
              arrowprops=dict(arrowstyle="<->", color="#FF6F00", lw=2.2))
ax3a.text(1.08, 0, f"Eye Height\n= {eh5:.4f}", color="#FF6F00",
          fontsize=8.5, va="center")

# Upper noise margin arrow
ax3a.annotate("", xy=(1.3, 0), xytext=(1.3, nm5),
              arrowprops=dict(arrowstyle="<->", color="#43A047", lw=1.8))
ax3a.text(1.33, nm5/2, f"Noise Margin\n= {nm5:.4f}", color="#43A047",
          fontsize=8, va="center")

ax3a.set_title("Task 3(a,b,c) — Eye Diagram at SNR = 5 dB\n"
               "Binary PAM, α = 0.32, Matched Filter Output\n"
               "Eye Height, Noise Margin & Optimum Sampling Instant annotated")
ax3a.set_xlabel("Normalised Time  (Symbol Intervals Ts)")
ax3a.set_ylabel("Amplitude")
ax3a.legend(fontsize=9, loc="upper right")
ax3a.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
fig3a.savefig("Task3_EyeDiagram_5dB_Annotated.png", bbox_inches="tight")
print("\n[Task 3] Annotated eye diagram @ 5 dB => Task3_EyeDiagram_5dB_Annotated.png")
plt.close()

# ── Figure 3b: Comparative Eye Diagrams (0, 5, 10, 15 dB) ───
fig3b, axes3b = plt.subplots(2, 2, figsize=(14, 9))
axes3b = axes3b.flatten()

for ax_idx, (snr_v, col) in enumerate(zip(SNR_LEVELS, EYE_COLORS)):
    d = eye_data[snr_v]
    for seg in d["segs"]:
        ta = np.linspace(0, 2, len(seg))
        axes3b[ax_idx].plot(ta, seg, color=col, alpha=0.09, linewidth=0.7)

    axes3b[ax_idx].axvline(1.0, color="lime", linewidth=1.3, linestyle="--",
                           label="Opt. Instant = 1.0 Ts")
    axes3b[ax_idx].axhline(0, color="k", linewidth=0.4, linestyle=":")
    axes3b[ax_idx].set_title(
        f"SNR = {snr_v} dB  |  BER = {d['BER']:.6f}\n"
        f"Eye Height = {d['EyeHeight']:.4f}   Eye Width = {d['EyeWidth']:.3f} Ts\n"
        f"Noise Margin = {d['NoiseMargin']:.4f}"
    )
    axes3b[ax_idx].set_xlabel("Normalised Time (Symbol Intervals)")
    axes3b[ax_idx].set_ylabel("Amplitude")
    axes3b[ax_idx].legend(fontsize=7, loc="upper right")
    axes3b[ax_idx].grid(True, linestyle="--", alpha=0.4)

fig3b.suptitle(
    "Task 3(d) — Comparative Eye Diagrams  (Binary PAM, α = 0.32)\n"
    "SNR = 0, 5, 10, 15 dB — Matched Filter Output",
    fontsize=13, fontweight="bold"
)
plt.tight_layout()
fig3b.savefig("Task3_EyeDiagrams_Comparison.png", bbox_inches="tight")
print("[Task 3] Comparative eye diagrams => Task3_EyeDiagrams_Comparison.png")
plt.close()


# ╔══════════════════════════════════════════════════════════════╗
# ║                     TASK  4                                  ║
# ║    RC Pulse Analysis for alpha = 0, 0.75, 1.0               ║
# ╚══════════════════════════════════════════════════════════════╝
print("\n"+"="*65)
print("  TASK 4: RC Pulse Analysis — alpha = 0, 0.75, 1.0")
print("="*65)


def make_rc_pulse(alpha_val, m_val=10, l_val=5):
    n_idx  = np.arange(0, 2*l_val*m_val + 1)
    t_n    = n_idx / m_val - l_val
    den    = 1 - 4*(alpha_val**2)*(t_n**2)
    den    = np.where(np.abs(den) < 1e-10, 1e-10, den)
    if alpha_val == 0.0:
        pulse = np.sinc(t_n)
    else:
        pulse = np.sinc(t_n) * np.cos(np.pi*alpha_val*t_n) / den
    return t_n, pulse


ALPHA_VALS = [0.0, 0.75, 1.0]
COLORS_A   = ["#1565C0", "#E65100", "#2E7D32"]
LABELS_A   = [r"$\alpha$ = 0  (ideal sinc, Nyquist min BW)",
               r"$\alpha$ = 0.75",
               r"$\alpha$ = 1.0  (full roll-off, double BW)"]

# ── Figure 4a: RC Pulse Shape Comparison ─────────────────────
fig4a, ax4a = plt.subplots(figsize=(11, 5))
for av, col, lbl in zip(ALPHA_VALS, COLORS_A, LABELS_A):
    t_n, pulse_v = make_rc_pulse(av)
    ax4a.plot(t_n, pulse_v, color=col, linewidth=2.2, label=lbl)

ax4a.axhline(0, color="k", linewidth=0.7, linestyle="--")
ax4a.set_title("Task 4 — Raised-Cosine Pulse Shapes for α = 0, 0.75, 1.0\n"
               "(FIR TDL Model, m = 10, l = 5  →  101 taps)")
ax4a.set_xlabel("Normalised Time  (t / T_b)")
ax4a.set_ylabel("Amplitude  p_n")
ax4a.set_xlim(-5, 5)
ax4a.set_ylim(-0.35, 1.15)
ax4a.legend(fontsize=10)
ax4a.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
fig4a.savefig("Task4_RC_Pulse_Comparison.png", bbox_inches="tight")
print("\n[Task 4] RC pulse shape comparison => Task4_RC_Pulse_Comparison.png")
plt.close()

# ── Figure 4b: BW vs alpha ────────────────────────────────────
alpha_cont = np.linspace(0, 1, 300)
BW_total   = (1 + alpha_cont) / 2.0
BW_excess  = alpha_cont / 2.0

fig4b, ax4b = plt.subplots(figsize=(9, 5))
ax4b.plot(alpha_cont, BW_total,  color="#1565C0", linewidth=2.2,
          label=r"Total BW = $(1+\alpha)/(2T_b)$")
ax4b.plot(alpha_cont, BW_excess, color="#D32F2F", linewidth=2.0,
          linestyle="--", label=r"Excess BW = $\alpha/(2T_b)$")
ax4b.axhline(0.5, color="gray", linewidth=1.0, linestyle=":",
             label=r"Nyquist min BW = $1/(2T_b)$")

for av, col in zip(ALPHA_VALS, COLORS_A):
    bw_v = (1+av)/2.0
    ax4b.plot(av, bw_v, "o", color=col, markersize=10, zorder=5)
    ax4b.annotate(f"α={av}\nBW={bw_v:.2f}/T_b",
                  xy=(av, bw_v),
                  xytext=(av+0.05, bw_v-0.08),
                  fontsize=8.5, color=col,
                  arrowprops=dict(arrowstyle="->", color=col, lw=1.2))

ax4b.set_title("Task 4 — Bandwidth vs Roll-Off Factor α\n"
               "(Raised-Cosine Pulse, Binary PAM)")
ax4b.set_xlabel("Roll-Off Factor  α")
ax4b.set_ylabel("Normalised One-Sided BW  [× 1/T_b]")
ax4b.legend(fontsize=9)
ax4b.grid(True, linestyle="--", alpha=0.6)
ax4b.set_xlim(0, 1)
ax4b.set_ylim(0.30, 1.10)
plt.tight_layout()
fig4b.savefig("Task4_BW_vs_Alpha.png", bbox_inches="tight")
print("[Task 4] BW vs alpha => Task4_BW_vs_Alpha.png")
plt.close()

# BW table
print("\n--- Task 4: Bandwidth Summary Table ---")
print(f"{'α':>8}  {'Total BW (×1/Tb)':>20}  {'Excess BW (×1/Tb)':>20}  {'% Excess BW':>13}")
print("-"*68)
for av in [0.00, 0.25, 0.32, 0.50, 0.75, 1.00]:
    bw_t = (1+av)/2.0
    bw_e = av/2.0
    note = "← Nyquist min" if av == 0.00 else ("← design α" if av == 0.32 else
           ("← Task 4 key" if av in [0.75, 1.00] else ""))
    print(f"{av:>8.2f}  {bw_t:>20.4f}  {bw_e:>20.4f}  {av*100:>12.1f}%  {note}")

# ── Figure 4c: BER vs alpha (SNR = 5 dB) ─────────────────────
alpha_sweep = np.linspace(0.0, 1.0, 21)
ber_alpha   = []

print("\n--- Task 4: BER vs Alpha (SNR = 5 dB) ---")
print(f"{'α':>8}  {'BER (Simulated)':>18}")
print("-"*30)

for av in alpha_sweep:
    _, pulse_v = make_rc_pulse(av)
    ups_a      = np.zeros(num_bits*m)
    ups_a[::m] = symbols
    tx_a       = np.convolve(ups_a, pulse_v, mode="full")
    _, _, _, ber_a = simulate_binary_pam(tx_a, 5.0, pulse_v, m, bits)
    ber_alpha.append(ber_a)
    print(f"{av:>8.3f}  {ber_a:>18.6f}")

fig4c, ax4c = plt.subplots(figsize=(9, 5))
ax4c.semilogy(alpha_sweep, [max(b, 1e-7) for b in ber_alpha],
              "ms-", linewidth=2.0, markersize=7,
              label="Simulated BER  @ SNR = 5 dB")
for av, col, lbl in zip(ALPHA_VALS, COLORS_A, LABELS_A):
    ax4c.axvline(av, color=col, linestyle="--", linewidth=1.5,
                 label=f"α = {av}  (BW = {(1+av)/2:.2f}/T_b)")
ax4c.set_title("Task 4 — BER vs Roll-Off Factor α\n"
               "(Binary PAM, AWGN, SNR = 5 dB)")
ax4c.set_xlabel("Roll-Off Factor  α")
ax4c.set_ylabel("Bit Error Rate (BER)")
ax4c.legend(fontsize=8.5)
ax4c.grid(True, which="both", linestyle="--", alpha=0.6)
ax4c.set_xlim(0, 1)
plt.tight_layout()
fig4c.savefig("Task4_BER_vs_Alpha.png", bbox_inches="tight")
print("\n[Task 4] BER vs alpha => Task4_BER_vs_Alpha.png")
plt.close()

# ── Figure 4d: Eye diagrams for alpha = 0, 0.75, 1.0 @ SNR = 5 dB ─
fig4d, axes4d = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

print("\n--- Task 4: Eye Parameters for alpha = 0, 0.75, 1.0 @ SNR = 5 dB ---")
print(f"{'α':>8}  {'Eye Height':>12}  {'Eye Width':>12}  {'Noise Margin':>14}  {'BER':>12}")
print("-"*65)

for ax_i, (av, col, lbl) in enumerate(zip(ALPHA_VALS, COLORS_A, LABELS_A)):
    _, pulse_v = make_rc_pulse(av)
    ups_a = np.zeros(num_bits*m); ups_a[::m] = symbols
    tx_a  = np.convolve(ups_a, pulse_v, mode="full")
    _, mf_a, _, ber_a = simulate_binary_pam(tx_a, 5.0, pulse_v, m, bits)
    segs_a, eh_a, ew_a, nm_a, oi_a = extract_eye_params(mf_a, m)

    for seg in segs_a:
        ta = np.linspace(0, 2, len(seg))
        axes4d[ax_i].plot(ta, seg, color=col, alpha=0.08, linewidth=0.7)

    axes4d[ax_i].axvline(1.0, color="lime", linewidth=1.4, linestyle="--")
    axes4d[ax_i].axhline(0, color="k", linewidth=0.5, linestyle=":")
    axes4d[ax_i].set_title(
        f"α = {av}\nEye H = {eh_a:.4f}  NM = {nm_a:.4f}\nBER = {ber_a:.6f}"
    )
    axes4d[ax_i].set_xlabel("Normalised Time (Ts)")
    axes4d[ax_i].grid(True, linestyle="--", alpha=0.4)
    print(f"{av:>8.2f}  {eh_a:>12.4f}  {ew_a:>12.4f}  {nm_a:>14.4f}  {ber_a:>12.6f}")

axes4d[0].set_ylabel("Amplitude")
fig4d.suptitle(
    "Task 4 — Eye Diagrams for α = 0, 0.75, 1.0  (SNR = 5 dB)\n"
    "Effect of Roll-Off Factor on Eye Opening & Noise Margin",
    fontsize=12, fontweight="bold"
)
plt.tight_layout()
fig4d.savefig("Task4_EyeDiagrams_Alpha.png", bbox_inches="tight")
print("\n[Task 4] Eye diagrams (alpha comparison) => Task4_EyeDiagrams_Alpha.png")
plt.close()

print("\n"+"="*65)
print("  All Task 3 & Task 4 figures generated successfully.")
print("="*65)
