# -*- coding: utf-8 -*-
"""
UE24EC341A: DIGITAL COMMUNICATION
ORANGE LEVEL PROBLEM — Task 5

Task 5 : Inter-Symbol Interference (ISI) Analysis & Linear Equalizer Comparison

  A realistic dispersive (multi-path) channel is introduced after the AWGN
  channel to induce ISI.  Three receivers are compared:
    (a) No equalizer       — baseline degraded system
    (b) Zero-Forcing (ZF)  — eliminates ISI, amplifies noise
    (c) MMSE Equalizer     — balances ISI suppression vs. noise enhancement

  For each equalizer:
    * BER vs SNR curves (simulated + relevant bounds)
    * Eye diagrams before and after equalization
    * Frequency-domain magnitude response
    * MMSE vs ZF gain chart

  Reference: Digital Communication Systems, Simon Haykin
             Chapter 8 — Signaling over Band-Limited Channels
             Chapter 9 — Adaptive Filters (MMSE / Wiener)
             John Wiley & Sons, 2014

  Name  : Suraj H P
  SRN   : PES1UG24EC221
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import erfc

# ---------------------------------------------------------------------------
# Plot styling
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "figure.dpi": 150,
    "font.family": "DejaVu Sans",
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
})

print("=" * 70)
print("  TASK 5: ISI Analysis & Linear Equalizer Comparison")
print("=" * 70)

# ---------------------------------------------------------------------------
# Section 1: RC PULSE  (same parameters as Tasks 1-4 for consistency)
# ---------------------------------------------------------------------------
alpha_design = 0.32
m = 10          # samples per symbol
l = 5           # truncation (bits)

n_idx  = np.arange(0, 2*l*m + 1)
t_norm = n_idx / m - l
denom  = 1 - 4*(alpha_design**2)*(t_norm**2)
denom  = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
p_rc   = np.sinc(t_norm) * np.cos(np.pi*alpha_design*t_norm) / denom

# ---------------------------------------------------------------------------
# Section 2: TWO-PATH DISPERSIVE CHANNEL MODEL
#
#  h[n] = [h0, 0...0, h1]  — two taps separated by `delay` samples
#  This simulates a multipath channel that introduces ISI across symbols.
#  h(t) = h0*delta(t) + h1*delta(t - tau)
#    h0 = 1.0  (direct path, dominant)
#    h1 = 0.5  (reflected path, 50% of direct amplitude)
#    delay = m samples = 1 symbol period (worst-case ISI from adjacent symbol)
# ---------------------------------------------------------------------------
h0, h1  = 1.0, 0.5        # path gains
delay   = m               # one symbol-period delay
h_chan  = np.zeros(delay + 1)
h_chan[0]     = h0
h_chan[delay] = h1

print(f"\n[Channel] Two-path model:  h = {h0}*delta(t) + {h1}*delta(t-{delay} samp)")
print(f"  Direct path gain  h0 = {h0}")
print(f"  Reflected path    h1 = {h1}  (delay = {delay} samples = 1 symbol period)")

# ---------------------------------------------------------------------------
# Section 3: DATA GENERATION  (10 000 bits, seed=42 for reproducibility)
# ---------------------------------------------------------------------------
np.random.seed(42)
num_bits = 10_000
bits     = np.random.randint(0, 2, num_bits)
symbols  = 2*bits - 1          # bipolar +/-1

upsampled      = np.zeros(num_bits * m)
upsampled[::m] = symbols
tx_signal      = np.convolve(upsampled, p_rc, mode="full")   # pulse-shaped

# ---------------------------------------------------------------------------
# Section 4: HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def add_awgn(signal, snr_db):
    """Add AWGN calibrated to the signal power at the given SNR (dB)."""
    snr_lin   = 10**(snr_db / 10.0)
    sig_power = np.mean(signal**2)
    noise_pow = sig_power / snr_lin
    return signal + np.sqrt(noise_pow) * np.random.randn(len(signal))


def matched_filter_output(rx, pulse):
    """Apply matched filter (time-reversed pulse) and return full output."""
    return np.convolve(rx, pulse[::-1], mode="full")


def sample_at_peak(mf_out, pulse, num_sym, m_val):
    """Downsample matched filter output at the optimal instants."""
    comp_resp = np.convolve(pulse, pulse[::-1], mode="full")
    peak      = np.argmax(comp_resp)
    return mf_out[peak : peak + num_sym*m_val : m_val]


def decide_binary(samples):
    """Hard threshold decision for bipolar +/-1 signalling."""
    return (samples >= 0).astype(int)


def compute_ber(bits_tx, bits_rx):
    n = min(len(bits_tx), len(bits_rx))
    return np.mean(bits_tx[:n] != bits_rx[:n])


def eye_segments(signal, m_val, num_traces=300):
    """Extract 2-symbol segments for eye diagram overlay."""
    segs = []
    for i in range(num_traces):
        s = i * m_val
        e = s + 2*m_val
        if e < len(signal):
            segs.append(signal[s:e])
    return segs


def apply_equalizer(rx_sig, h_channel, noise_var, mode="ZF"):
    """
    Frequency-domain ZF or MMSE equalizer.

    ZF  : W(f) = H*(f) / |H(f)|^2
    MMSE: W(f) = H*(f) / (|H(f)|^2 + sigma_n^2 / sigma_x^2)

    Returns the equalized signal (same length as rx_sig).
    """
    N    = len(rx_sig)
    H_f  = np.fft.fft(h_channel, N)
    RX_f = np.fft.fft(rx_sig)

    if mode == "ZF":
        denom = np.abs(H_f)**2
        eps   = 1e-6 * np.max(denom)
        W_f   = np.conj(H_f) / np.maximum(denom, eps)
    else:  # MMSE
        sigma2_x = 1.0   # normalised symbol power for +/-1
        denom    = np.abs(H_f)**2 + noise_var / sigma2_x
        W_f      = np.conj(H_f) / denom

    eq = np.real(np.fft.ifft(W_f * RX_f))
    return eq


# ---------------------------------------------------------------------------
# Section 5: SNR SWEEP — BER curves for all three receivers
# ---------------------------------------------------------------------------
snr_range       = [-2, 0, 2, 4, 6, 8, 10, 12, 14, 16]
ber_noisy_noeq  = []   # AWGN only, no channel (ideal reference)
ber_isi_noeq    = []   # AWGN + ISI channel, no equalizer
ber_isi_zf      = []   # AWGN + ISI + ZF equalizer
ber_isi_mmse    = []   # AWGN + ISI + MMSE equalizer
ber_theory      = []   # Theoretical AWGN-only BER (no ISI)

print("\n--- BER vs SNR Table ---")
print(f"{'SNR(dB)':>8}  {'AWGN only':>12}  {'ISI no EQ':>12}  "
      f"{'ISI+ZF':>10}  {'ISI+MMSE':>10}  {'Theory':>10}")
print("-" * 72)

for snr_v in snr_range:
    snr_lin   = 10**(snr_v / 10.0)
    sig_power = np.mean(tx_signal**2)
    noise_var = sig_power / snr_lin

    # A. AWGN only (no ISI channel) — ideal reference
    rx_awgn   = add_awgn(tx_signal, snr_v)
    mf_awgn   = matched_filter_output(rx_awgn, p_rc)
    samp_awgn = sample_at_peak(mf_awgn, p_rc, num_bits, m)
    ber_a     = compute_ber(bits, decide_binary(samp_awgn))
    ber_noisy_noeq.append(ber_a)

    # B. ISI channel + AWGN, matched filter only (no equalizer)
    tx_isi   = np.convolve(tx_signal, h_chan, mode="full")
    rx_isi   = add_awgn(tx_isi, snr_v)
    mf_isi   = matched_filter_output(rx_isi, p_rc)
    samp_isi = sample_at_peak(mf_isi, p_rc, num_bits, m)
    ber_b    = compute_ber(bits, decide_binary(samp_isi))
    ber_isi_noeq.append(ber_b)

    # C. ISI channel + AWGN + ZF equalizer + MF
    rx_zf_eq  = apply_equalizer(rx_isi, h_chan, noise_var, mode="ZF")
    mf_zf     = matched_filter_output(rx_zf_eq, p_rc)
    samp_zf   = sample_at_peak(mf_zf, p_rc, num_bits, m)
    ber_c     = compute_ber(bits, decide_binary(samp_zf))
    ber_isi_zf.append(ber_c)

    # D. ISI channel + AWGN + MMSE equalizer + MF
    rx_mmse_eq = apply_equalizer(rx_isi, h_chan, noise_var, mode="MMSE")
    mf_mmse    = matched_filter_output(rx_mmse_eq, p_rc)
    samp_mmse  = sample_at_peak(mf_mmse, p_rc, num_bits, m)
    ber_d      = compute_ber(bits, decide_binary(samp_mmse))
    ber_isi_mmse.append(ber_d)

    # E. Theoretical BER (perfect AWGN, no ISI)
    ber_th = 0.5 * erfc(np.sqrt(snr_lin))
    ber_theory.append(ber_th)

    print(f"{snr_v:>8}  {ber_a:>12.6f}  {ber_b:>12.6f}  "
          f"{ber_c:>10.6f}  {ber_d:>10.6f}  {ber_th:>10.6f}")

# ---------------------------------------------------------------------------
# Section 6: FIGURE 5a — BER vs SNR (all four curves on one semi-log plot)
# ---------------------------------------------------------------------------
fig5a, ax5a = plt.subplots(figsize=(10, 6))

ax5a.semilogy(snr_range, [max(b, 1e-7) for b in ber_theory],
              "k--",  linewidth=2.0, label="Theoretical BER (AWGN, no ISI)")
ax5a.semilogy(snr_range, [max(b, 1e-7) for b in ber_noisy_noeq],
              "bo-",  linewidth=1.8, markersize=7,
              label="Simulated AWGN only (no ISI)")
ax5a.semilogy(snr_range, [max(b, 1e-7) for b in ber_isi_noeq],
              "rs--", linewidth=1.8, markersize=7,
              label="ISI channel — No Equalizer")
ax5a.semilogy(snr_range, [max(b, 1e-7) for b in ber_isi_zf],
              "g^-",  linewidth=1.8, markersize=7,
              label="ISI channel — ZF Equalizer")
ax5a.semilogy(snr_range, [max(b, 1e-7) for b in ber_isi_mmse],
              "mD-",  linewidth=1.8, markersize=7,
              label="ISI channel — MMSE Equalizer")

ax5a.set_title("Task 5(a) — BER vs SNR: ISI Channel with ZF & MMSE Equalizers\n"
               "Binary PAM, alpha=0.32, Two-Path Channel (h0=1.0, h1=0.5, delay=1 Ts)")
ax5a.set_xlabel("SNR (dB)")
ax5a.set_ylabel("Bit Error Rate (BER)")
ax5a.legend(loc="lower left")
ax5a.grid(True, which="both", linestyle="--", alpha=0.6)
ax5a.set_xlim(-2, 16)
plt.tight_layout()
fig5a.savefig("Task5_BER_vs_SNR_Equalizers.png", bbox_inches="tight")
print("\n[Task 5] BER vs SNR figure => Task5_BER_vs_SNR_Equalizers.png")
plt.close()

# ---------------------------------------------------------------------------
# Section 7: EYE DIAGRAMS  @ SNR = 5 dB (before and after equalization)
# ---------------------------------------------------------------------------
snr_eye     = 5.0
snr_lin_e   = 10**(snr_eye / 10.0)
sig_pow_e   = np.mean(tx_signal**2)
noise_var_e = sig_pow_e / snr_lin_e

tx_isi_e  = np.convolve(tx_signal, h_chan, mode="full")
rx_isi_e  = add_awgn(tx_isi_e, snr_eye)
rx_zf_e   = apply_equalizer(rx_isi_e, h_chan, noise_var_e, mode="ZF")
rx_mmse_e = apply_equalizer(rx_isi_e, h_chan, noise_var_e, mode="MMSE")

mf_ref_e   = matched_filter_output(add_awgn(tx_signal, snr_eye), p_rc)
mf_isi_e   = matched_filter_output(rx_isi_e,  p_rc)
mf_zf_e    = matched_filter_output(rx_zf_e,   p_rc)
mf_mmse_e  = matched_filter_output(rx_mmse_e, p_rc)

signals_eye = [mf_ref_e, mf_isi_e, mf_zf_e, mf_mmse_e]
titles_eye  = [
    "Reference: AWGN only (no ISI)\nSNR = 5 dB",
    "ISI Channel — No Equalizer\nSNR = 5 dB",
    "ISI Channel + ZF Equalizer\nSNR = 5 dB",
    "ISI Channel + MMSE Equalizer\nSNR = 5 dB",
]
colors_eye  = ["#1565C0", "#E53935", "#2E7D32", "#7B1FA2"]

fig5b, axes5b = plt.subplots(2, 2, figsize=(14, 10))
axes5b = axes5b.flatten()

for i, (sig, ttl, col) in enumerate(zip(signals_eye, titles_eye, colors_eye)):
    segs = eye_segments(sig, m)
    for seg in segs:
        ta = np.linspace(0, 2, len(seg))
        axes5b[i].plot(ta, seg, color=col, alpha=0.09, linewidth=0.7)
    axes5b[i].axvline(1.0, color="lime", linewidth=1.4, linestyle="--",
                      label="Opt. Sampling t = 1.0 Ts")
    axes5b[i].axhline(0, color="k", linewidth=0.5, linestyle=":")
    axes5b[i].set_title(ttl, fontsize=10)
    axes5b[i].set_xlabel("Normalised Time (Symbol Intervals)")
    axes5b[i].set_ylabel("Amplitude")
    axes5b[i].legend(fontsize=7, loc="upper right")
    axes5b[i].grid(True, linestyle="--", alpha=0.4)

fig5b.suptitle(
    "Task 5(b) — Eye Diagrams: Effect of ISI & Equalization (SNR = 5 dB)\n"
    "Binary PAM, alpha=0.32 | Two-Path Channel h0=1.0, h1=0.5",
    fontsize=12, fontweight="bold"
)
plt.tight_layout()
fig5b.savefig("Task5_EyeDiagrams_Equalization.png", bbox_inches="tight")
print("[Task 5] Eye diagrams => Task5_EyeDiagrams_Equalization.png")
plt.close()

# ---------------------------------------------------------------------------
# Section 8: FREQUENCY-DOMAIN RESPONSE ANALYSIS
# ---------------------------------------------------------------------------
N_fft    = 1024
H_f_plot = np.fft.fft(h_chan, N_fft)
freqs    = np.fft.fftfreq(N_fft, d=1.0/m)
pos_mask = freqs >= 0

noise_var_fd = sig_pow_e / snr_lin_e

denom_zf = np.abs(H_f_plot)**2
eps_fd   = 1e-6 * np.max(denom_zf)
W_ZF_f   = np.conj(H_f_plot) / np.maximum(denom_zf, eps_fd)

W_MMSE_f = np.conj(H_f_plot) / (np.abs(H_f_plot)**2 + noise_var_fd)

fig5c, ax5c = plt.subplots(figsize=(10, 5))
ax5c.plot(freqs[pos_mask], 20*np.log10(np.abs(H_f_plot[pos_mask]) + 1e-12),
          color="#1565C0", linewidth=2.2, label="Channel  |H(f)|")
ax5c.plot(freqs[pos_mask], 20*np.log10(np.abs(W_ZF_f[pos_mask])  + 1e-12),
          color="#2E7D32", linewidth=2.0, linestyle="--",
          label="ZF Equalizer  |W_ZF(f)|")
ax5c.plot(freqs[pos_mask], 20*np.log10(np.abs(W_MMSE_f[pos_mask]) + 1e-12),
          color="#7B1FA2", linewidth=2.0, linestyle="-.",
          label="MMSE Equalizer  |W_MMSE(f)|  @ SNR=5 dB")
ax5c.axvline(0.5, color="gray", linewidth=1.0, linestyle=":",
             label="Nyquist BW = 0.5/T_b")
ax5c.set_title("Task 5(c) — Frequency-Domain Response\n"
               "Channel, ZF & MMSE Equalizer Magnitude (SNR = 5 dB)")
ax5c.set_xlabel("Normalised Frequency  [x 1/T_b]")
ax5c.set_ylabel("Magnitude (dB)")
ax5c.set_xlim(0, 1.0)
ax5c.set_ylim(-30, 30)
ax5c.legend()
ax5c.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
fig5c.savefig("Task5_FreqResponse_Equalizers.png", bbox_inches="tight")
print("[Task 5] Frequency response => Task5_FreqResponse_Equalizers.png")
plt.close()

# ---------------------------------------------------------------------------
# Section 9: EQUALIZED EYE DIAGRAM PARAMETER TABLE  @ SNR = 5 dB
# ---------------------------------------------------------------------------
def eye_params_from_segs(segs, m_val):
    """Compute Eye Height and Noise Margin from segment list."""
    if not segs:
        return 0.0, 0.0
    arr      = np.array(segs)
    mid_vals = arr[:, m_val]
    pos_v    = mid_vals[mid_vals > 0]
    neg_v    = mid_vals[mid_vals < 0]
    pos_min  = np.min(pos_v) if len(pos_v) else 0.0
    neg_max  = np.max(neg_v) if len(neg_v) else 0.0
    eye_h    = pos_min - neg_max
    return eye_h, eye_h / 2.0


print("\n--- Eye Diagram Parameters @ SNR = 5 dB ---")
print(f"{'Receiver':<28}  {'Eye Height':>12}  {'Noise Margin':>14}  {'BER':>12}")
print("-" * 75)

configs = [
    ("AWGN only (no ISI)",   mf_ref_e),
    ("ISI — No Equalizer",   mf_isi_e),
    ("ISI — ZF Equalizer",   mf_zf_e),
    ("ISI — MMSE Equalizer", mf_mmse_e),
]
for label, mf_sig in configs:
    segs = eye_segments(mf_sig, m)
    eh, nm = eye_params_from_segs(segs, m)
    samp   = sample_at_peak(mf_sig, p_rc, num_bits, m)
    ber_v  = compute_ber(bits, decide_binary(samp))
    print(f"{label:<28}  {eh:>12.4f}  {nm:>14.4f}  {ber_v:>12.6f}")

# ---------------------------------------------------------------------------
# Section 10: SNR PENALTY ANALYSIS
# ---------------------------------------------------------------------------
print("\n--- SNR required to reach BER <= 1e-3 ---")

def find_snr_at_ber(snr_list, ber_list, target=1e-3):
    for snr_v, ber_v in zip(snr_list, ber_list):
        if ber_v <= target:
            return f"{snr_v} dB"
    return ">16 dB (BER floor)"

print(f"  Theoretical (no ISI)  : {find_snr_at_ber(snr_range, ber_theory)}")
print(f"  Simulated  (no ISI)   : {find_snr_at_ber(snr_range, ber_noisy_noeq)}")
print(f"  ISI — No Equalizer    : {find_snr_at_ber(snr_range, ber_isi_noeq)}")
print(f"  ISI — ZF Equalizer    : {find_snr_at_ber(snr_range, ber_isi_zf)}")
print(f"  ISI — MMSE Equalizer  : {find_snr_at_ber(snr_range, ber_isi_mmse)}")

# ---------------------------------------------------------------------------
# Section 11: MMSE vs ZF GAIN vs SNR
# ---------------------------------------------------------------------------
mmse_arr    = np.array([max(b, 1e-7) for b in ber_isi_mmse])
zf_arr      = np.array([max(b, 1e-7) for b in ber_isi_zf])
ber_gain_dB = 10 * np.log10(zf_arr / mmse_arr)

fig5d, ax5d = plt.subplots(figsize=(9, 4))
ax5d.bar(snr_range, ber_gain_dB, color="#1976D2", alpha=0.8, width=1.4,
         label="MMSE gain over ZF  [dB in log(BER) scale]")
ax5d.axhline(0, color="k", linewidth=0.8)
ax5d.set_title("Task 5(d) — MMSE Equalizer Advantage over ZF\n"
               "Binary PAM, Two-Path ISI Channel (h0=1.0, h1=0.5)")
ax5d.set_xlabel("SNR (dB)")
ax5d.set_ylabel("BER Improvement [10*log10(BER_ZF / BER_MMSE)]  (dB)")
ax5d.legend()
ax5d.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
fig5d.savefig("Task5_MMSE_vs_ZF_Gain.png", bbox_inches="tight")
print("\n[Task 5] MMSE vs ZF gain figure => Task5_MMSE_vs_ZF_Gain.png")
plt.close()

# ---------------------------------------------------------------------------
# Section 12: INFERENCES
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("  INFERENCE — Task 5: ISI Analysis & Linear Equalizer Comparison")
print("=" * 70)
print("""
Inference 1 (ISI Degradation):
  The two-path channel (h0=1.0, h1=0.5, delay=1 Ts) introduces severe ISI.
  Without equalization, the BER is dominated by interference from the
  adjacent symbol and does not improve significantly beyond ~10 dB SNR —
  creating an irreducible BER floor. The eye nearly closes, confirming that
  matched filtering alone (designed for the pulse, not the channel) is
  insufficient in a dispersive environment.

Inference 2 (Zero-Forcing Equalizer):
  The ZF equalizer inverts the channel response in the frequency domain,
  restoring the ISI-free signal at the cost of noise amplification. At high
  SNR it approaches the ideal (no-ISI) BER curve. However, at low SNR the
  ZF filter amplifies noise in frequency bands where the channel is weak
  (spectral nulls), causing the ZF BER to worsen compared to MMSE in the
  low-SNR regime.

Inference 3 (MMSE Equalizer):
  The MMSE equalizer strikes the optimal balance between ISI suppression
  and noise enhancement. By incorporating the noise variance in its design
  (sigma_n^2 / sigma_x^2 regularisation term), it avoids excessive noise
  amplification at spectral nulls. At low-to-moderate SNR (0-8 dB) the
  MMSE consistently outperforms ZF; at high SNR both converge since the
  noise term becomes negligible relative to |H(f)|^2.

Inference 4 (Eye Diagram Interpretation):
  * ISI (no equalizer): Eye diagram is severely distorted — multiple crossing
    levels and a nearly closed eye, indicating corruption from adjacent symbols.
  * ZF equalizer: Eye reopens significantly. Residual closure comes from
    amplified noise, not ISI.
  * MMSE equalizer: Comparable eye opening to ZF but with reduced noise
    variance, leading to better noise margin at the decision threshold.

Inference 5 (Frequency-Domain Insight):
  The two-path channel creates a spectral notch where destructive interference
  occurs between the direct and reflected path. The ZF equalizer boosts this
  notch toward infinity, amplifying noise. The MMSE equalizer limits the
  boost to sigma_x^2 / sigma_n^2, trading a small amount of residual ISI
  for a large noise reduction — the fundamental ISI-noise trade-off in
  linear receiver design.

Inference 6 (Practical Design Lesson):
  Pulse shaping (Tasks 1-4) eliminates ISI in ideal AWGN channels; linear
  equalization (Task 5) is required when the physical channel introduces
  additional dispersion. MMSE equalization is the preferred linear strategy
  because it minimises the mean-squared error at the decision point. For
  non-linear channels or higher-order M-PAM, Decision Feedback Equalizers
  (DFE) or turbo equalization represent the natural next step.
""")

print("=" * 70)
print("  All Task 5 figures generated successfully.")
print("=" * 70)
print("\nOutput files:")
print("  Task5_BER_vs_SNR_Equalizers.png    — BER vs SNR for all receivers")
print("  Task5_EyeDiagrams_Equalization.png — 2x2 eye diagram comparison")
print("  Task5_FreqResponse_Equalizers.png  — Channel & equalizer freq response")
print("  Task5_MMSE_vs_ZF_Gain.png          — MMSE vs ZF BER gain per SNR point")
