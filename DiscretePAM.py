# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 13:03:36 2026

@author: Vamsi
"""

import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. Generate and Plot RC Pulse (Figure 8.8)
# ==========================================
alpha = 0.32  # Roll-off factor
m = 10        # Number of FIR samples per bit[cite: 6]
l = 5         # Truncation parameter (half duration in bits)[cite: 5]

n_indices = np.arange(0, 2 * l * m + 1)
t_norm = n_indices / m - l

# Discretized causal RC pulse formula (Eq. 8.32)[cite: 4]
denom = 1 - 4 * (alpha ** 2) * (t_norm ** 2)
denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
p = np.sinc(t_norm) * np.cos(np.pi * alpha * t_norm) / denom

# Plot Figure 8.8: Discretized RC pulse
plt.figure(figsize=(10, 4))
plt.stem(n_indices / m, p, basefmt="k-", linefmt="k-", markerfmt="ko")
plt.title("Discretized RC Pulse, computed using the TDL (Figure 8.8)[cite: 6]")
plt.xlabel("Time, n")
plt.ylabel("Amplitude")
plt.grid(True, linestyle="--")
plt.xlim(0, 2 * l)
plt.ylim(-0.2, 1.2)
plt.tight_layout()
plt.show()

# ==========================================
# 2. 4-PAM Symbol Generation & Mapping
# ==========================================
np.random.seed(42)
M = 4                     # Alphabet size for 4-PAM
bits_per_symbol = int(np.log2(M))

num_symbols = 500
num_bits = num_symbols * bits_per_symbol
bits = np.random.randint(0, 2, num_bits)

symbol_indices = bits.reshape(-1, bits_per_symbol).dot(
    1 << np.arange(bits_per_symbol)[::-1]
)
pam_levels = np.array([-3, -1, 1, 3])
symbols = pam_levels[symbol_indices]

# Normalize symbol power for fair comparison
avg_symbol_power = np.mean(symbols ** 2)
symbols = symbols / np.sqrt(avg_symbol_power)
normalized_levels = pam_levels / np.sqrt(avg_symbol_power)

# Upsample and convolve with RC pulse
upsampled = np.zeros(num_symbols * m)
upsampled[::m] = symbols
tx_signal = np.convolve(upsampled, p, mode="full")

# ==========================================
# 3. Add AWGN for SNR = 5 dB
# ==========================================
snr_db = 5.0
snr_linear = 10 ** (snr_db / 10.0)

signal_power = np.mean(tx_signal ** 2)
noise_power = signal_power / snr_linear

noise = np.sqrt(noise_power) * np.random.randn(len(tx_signal))
rx_signal = tx_signal + noise

# ==========================================
# 4. Plot Transmitted & Noisy Received Signals
# ==========================================
plt.figure(figsize=(12, 6))
plot_samples = 30 * m
time_axis = np.arange(plot_samples) / m

plt.subplot(2, 1, 1)
plt.plot(time_axis, tx_signal[:plot_samples], color='b', linewidth=1.5)
plt.title("Transmitted 4-PAM Signal (Pulse Shaped)")
plt.xlabel("Time ($T_b$)")
plt.ylabel("Amplitude")
plt.grid(True, linestyle="--")

plt.subplot(2, 1, 2)
plt.plot(time_axis, rx_signal[:plot_samples], color='r', linewidth=1.0, alpha=0.8)
plt.title(f"Noisy Received Signal with AWGN (SNR = {snr_db} dB)")
plt.xlabel("Time ($T_b$)")
plt.ylabel("Amplitude")
plt.grid(True, linestyle="--")

plt.tight_layout()
plt.show()

# ==========================================
# 5. Matched Filtering & ML Decoding
# ==========================================
matched_filter_output = np.convolve(rx_signal, p[::-1], mode="full")

composite_response = np.convolve(p, p[::-1], mode="full")
peak_idx = np.argmax(composite_response)

rx_samples = matched_filter_output[peak_idx : peak_idx + num_symbols * m : m]

def ml_decode_4pam(received_vals, levels):
    distances = np.abs(received_vals[:, None] - levels[None, :])
    return np.argmin(distances, axis=1)

rx_symbol_indices = ml_decode_4pam(rx_samples, normalized_levels)

rx_bits = np.array(
    [
        [int(b) for b in np.binary_repr(idx, width=bits_per_symbol)]
        for idx in rx_symbol_indices
    ]
).flatten()

min_syms = min(len(symbol_indices), len(rx_symbol_indices))
ser = np.mean(symbol_indices[:min_syms] != rx_symbol_indices[:min_syms])

min_bits = min(len(bits), len(rx_bits))
ber = np.mean(bits[:min_bits] != rx_bits[:min_bits])

print(f"--- 4-PAM Simulation Results ---")
print(f"SNR: {snr_db} dB")
print(f"Total Symbols: {num_symbols}")
print(f"Symbol Error Rate (SER): {ser:.6f}")
print(f"Bit Error Rate (BER): {ber:.6f}")

# ==========================================
# 6. Eye Diagram Visualization
# ==========================================
def plot_eye_diagram(signal, m_val, num_traces=150):
    samples_per_eye = 2 * m_val
    plt.figure(figsize=(8, 4))
    for i in range(num_traces):
        start_idx = i * m_val
        end_idx = start_idx + samples_per_eye
        if end_idx < len(signal):
            segment = signal[start_idx:end_idx]
            t_axis = np.linspace(0, 2, len(segment))
            plt.plot(t_axis, segment, color="purple", alpha=0.1)

    plt.title("Eye Diagram of Matched Filter Output (4-PAM)")
    plt.xlabel("Normalized Time (Symbol Intervals)")
    plt.ylabel("Amplitude")
    plt.grid(True, linestyle="--")
    plt.tight_layout()
    plt.show()

plot_eye_diagram(matched_filter_output, m, num_traces=200)