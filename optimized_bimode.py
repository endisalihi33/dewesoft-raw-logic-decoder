# Made by Endi Salihi 
# All rights reserved 



import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt


zacetni_cas = time.perf_counter()


csv_file = 'digital.csv' # nujno poimenuj namesto [Channel 0]= [XDAT0] | [Channel 1]= [EN] | [Channel 2]= [CLK] | [Channel 3]= [XDAT1] !!!!! (ce imas drugace poglej DATASHEET)
df = pd.read_csv(csv_file, usecols=["Time [s]", "XDAT0", "EN", "CLK", "XDAT1"])

# glavna optimizirana stvar pretvorba v NumPy obedalvo brez loopa
cas_arr = df["Time [s]"].values
en_arr = df["EN"].values.astype(int)
clk_arr = df["CLK"].values.astype(int)
xdat0_arr = df["XDAT0"].values.astype(int)
xdat1_arr = df["XDAT1"].values.astype(int)

# tu gledamo kdaj pade EN na low a zacnemo brat podatke
padajoci_robovi = (en_arr[:-1] == 1) & (en_arr[1:] == 0)
zacetni_indeksi = np.where(padajoci_robovi)[0] + 1

# ce ni padajocega roba prekinemo
if len(zacetni_indeksi) == 0:
    raise ValueError("Ni padajočega roba na signalu EN.")


max_frejmov = 100000 # nastavi stevilo frejmov oz. samplov
zacetni_index = zacetni_indeksi[0]


en_segment = en_arr[zacetni_index:]
clk_segment = clk_arr[zacetni_index:]
xdat0_segment = xdat0_arr[zacetni_index:]
xdat1_segment = xdat1_arr[zacetni_index:]

# robovi rising za lovjenje clocka
clk_rising = (clk_segment[:-1] == 0) & (clk_segment[1:] == 1)
clk_rising_indexi = np.where(clk_rising)[0] + 1

# zdruzi pare iz podatkov v pravi vrstni red
bit_pari = (xdat0_segment[clk_rising_indexi] << 1) | xdat1_segment[clk_rising_indexi]


zlozeni_biti = np.empty(len(bit_pari) * 2, dtype=np.uint8)
zlozeni_biti[0::2] = (bit_pari >> 1) & 1  # XDAT0
zlozeni_biti[1::2] = bit_pari & 1        # XDAT1

# pretvrba bitov v bajte
uporabni_biti = (len(zlozeni_biti) // 8) * 8
bit_matrika = zlozeni_biti[:uporabni_biti].reshape(-1, 8)
bajt_vrednosti = np.packbits(bit_matrika, axis=1, bitorder='big').flatten()

# priprvi bajte za 24 bitno obdelavo
uporabni_bajti = (len(bajt_vrednosti) // 4) * 4
bajt_bloki = bajt_vrednosti[:uporabni_bajti].reshape(-1, 4)

# pretvori v little endian 
raw_vrednosti = (
    (bajt_bloki[:, 3].astype(np.uint32) << 24) |
    (bajt_bloki[:, 2].astype(np.uint32) << 16) |
    (bajt_bloki[:, 1].astype(np.uint32) << 8) |
    bajt_bloki[:, 0].astype(np.uint32)
)

# sign extend ker imamo signed vrednosti 24 bitne pospraulao pa v 32 bitov
signed_vrednosti = raw_vrednosti & 0xFFFFFF
signed_vrednosti = signed_vrednosti.astype(np.int32)
signed_vrednosti[signed_vrednosti & 0x800000 != 0] -= 0x1000000

# Kanali
st_kanalov = 8
st_frejmov = len(signed_vrednosti) // st_kanalov
kanal_matrika = signed_vrednosti[:st_frejmov * st_kanalov].reshape(-1, st_kanalov)


kanal_data = {k + 1: kanal_matrika[:, k] for k in range(st_kanalov)}

scale = 1.30548141896725e-6
offset = -0.0314681111488089263

pretvorjeni_kanali = {
    kanal_idx: scale * vrednosti + offset
    for kanal_idx, vrednosti in kanal_data.items()
}

koncni_cas = time.perf_counter()
print(f"Čas izvajanja: {koncni_cas - zacetni_cas:.6f} sekund")


plt.figure(figsize=(12, 6))
for kanal_idx, vrednosti in pretvorjeni_kanali.items():
    plt.plot(vrednosti, label=f'Kanal {kanal_idx}')
plt.title("Vrednosti vseh kanalov (v voltih)")
plt.xlabel("Frejmi")
plt.ylabel("Kanalne vrednosti (V)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

izbrani_kanal = 1
plt.figure(figsize=(10, 5))
plt.plot(pretvorjeni_kanali[izbrani_kanal], marker='o', markersize=2, linewidth=1)
plt.title(f"Kanal {izbrani_kanal} - Vrednosti (v voltih)")
plt.xlabel("Frejmi")
plt.ylabel("Vrednost (V)")
plt.grid(True)
plt.tight_layout()
plt.show()
