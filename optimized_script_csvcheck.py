import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time

# === CONFIGURATION ===
csv_file = '8xUNI_spiGlitch_2.csv'
frame_size_bits = 256
EN_ACTIVE_LOW = True
threshold = 100
selected_bytes = [0, 1, 2, 3]
frame_bytes = frame_size_bits // 8
MAX_FRAMES = 50000

# === EXECUTION START ===
start_time = time.time()

# Only load necessary columns
usecols = ["Time [s]", "EN", "CLK", "MOSI"]
df = pd.read_csv(csv_file, usecols=usecols)

# === Precompute edges ===
clk = df["CLK"].values
en = df["EN"].values
mosi = df["MOSI"].astype(np.uint8).values
time_s = df["Time [s]"].values

en_prev = np.roll(en, 1)
clk_prev = np.roll(clk, 1)

# Rising edges of CLK
clk_rising = (clk_prev == 0) & (clk == 1)

# EN active
en_active = (en == 0) if EN_ACTIVE_LOW else (en == 1)

# EN transition from inactive to active
en_went_active = ((en_prev == 1) & (en == 0)) if EN_ACTIVE_LOW else ((en_prev == 0) & (en == 1))

# Filtered indices
valid_indices = np.where(clk_rising & en_active)[0]

bitstream = []
timestamps = []
decoded_values = []

collecting = False
frame_start_time = 0

print("Starting decoding...")

for i in range(1, len(df)):
    if en_went_active[i]:
        collecting = True
        bitstream = []
        frame_start_time = time_s[i]

    if collecting and clk_rising[i] and en_active[i]:
        bitstream.append(mosi[i])

        if len(bitstream) == frame_size_bits:
            byte_list = [int(''.join(map(str, bitstream[j:j+8])), 2)
                         for j in range(0, frame_size_bits, 8)]

            selected = [byte_list[b] if b < len(byte_list) else 0 for b in selected_bytes]
            value = int.from_bytes(selected, byteorder='little', signed=True)

            decoded_values.append(value)
            timestamps.append(frame_start_time)

            if len(decoded_values) >= MAX_FRAMES:
                print(f"Reached MAX_FRAMES = {MAX_FRAMES}, stopping...")
                break

            collecting = False

# === Reporting ===
print("\nLarge jumps in decoded data:")
for i in range(1, len(decoded_values)):
    diff = abs(decoded_values[i] - decoded_values[i - 1])
    if diff > threshold:
        print(f"Frame {i}: Jump from {decoded_values[i - 1]} to {decoded_values[i]} (Δ = {diff}) at time {timestamps[i]:.9f}s")

end_time = time.time()
print(f"\nDecoded {len(decoded_values)} frames.")
print(f"Execution time: {end_time - start_time:.4f} seconds")

# === Plot ===
plt.figure(figsize=(10, 4))
plt.plot(timestamps, decoded_values, marker='.', linestyle='-')
plt.title("Decoded SPI Values (Bytes 0–3)")
plt.xlabel("Time [s]")
plt.ylabel("Signed Integer Value")
plt.grid(True)
plt.tight_layout()
plt.show()
