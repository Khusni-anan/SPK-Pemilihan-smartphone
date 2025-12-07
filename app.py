import streamlit as st
import pandas as pd
import numpy as np

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="SPK ARAS Smartphone",
    page_icon="📱",
    layout="wide"
)

# --- JUDUL & DESKRIPSI ---
st.title("📱 SPK Pemilihan Smartphone - Metode ARAS")
st.markdown("""
Aplikasi ini menggunakan metode **Additive Ratio Assessment (ARAS)** untuk merekomendasikan smartphone terbaik 
berdasarkan kriteria: **Harga (Cost), RAM, ROM, Baterai, dan Kamera (Benefit)**.
""")

# --- SIDEBAR (INPUT BOBOT) ---
st.sidebar.header("⚙️ Konfigurasi Bobot")
st.sidebar.info("Pastikan total bobot proporsional (Default total: 100%)")

w_harga = st.sidebar.slider("Bobot Harga (Cost)", 0.0, 0.5, 0.30, 0.05)
w_ram = st.sidebar.slider("Bobot RAM (Benefit)", 0.0, 0.5, 0.20, 0.05)
w_rom = st.sidebar.slider("Bobot ROM (Benefit)", 0.0, 0.5, 0.20, 0.05)
w_baterai = st.sidebar.slider("Bobot Baterai (Benefit)", 0.0, 0.5, 0.15, 0.05)
w_kamera = st.sidebar.slider("Bobot Kamera (Benefit)", 0.0, 0.5, 0.15, 0.05)

bobot = [w_harga, w_ram, w_rom, w_baterai, w_kamera]
total_bobot = sum(bobot)
st.sidebar.write(f"**Total Bobot:** {total_bobot:.2f}")

if total_bobot != 1.0:
    st.sidebar.warning("⚠️ Total bobot disarankan bernilai 1.0")

# --- DATA AWAL (DEFAULT) ---
data_awal = {
    'Alternative': ['Samsung Galaxy A54', 'Xiaomi 13T', 'Infinix GT 10 Pro', 'Realme 11 Pro'],
    'Price': [5.9, 6.5, 4.4, 5.5],        # Cost
    'RAM': [8, 12, 8, 12],                # Benefit
    'ROM': [256, 256, 256, 512],          # Benefit (Realme update ke 512)
    'Battery': [5000, 5000, 5000, 5000],  # Benefit
    'Camera': [50, 50, 108, 100]          # Benefit
}

# --- TAMPILAN TABEL EDITABLE ---
st.subheader("1. Data Alternatif Smartphone")
st.write("Anda bisa mengubah nilai di tabel ini secara langsung:")
df = pd.DataFrame(data_awal)
# Menggunakan st.data_editor agar user bisa edit data langsung di web
df_edit = st.data_editor(df, num_rows="dynamic", key="data_editor")

# --- PROSES PERHITUNGAN ARAS ---
if st.button("🚀 Hitung Rekomendasi"):
    
    # Pisahkan nama alternatif agar tidak ikut dihitung
    alternatives = df_edit['Alternative'].values
    matrix = df_edit.drop('Alternative', axis=1)
    cols = matrix.columns
    
    # Definisi Tipe Kriteria (Sesuai urutan kolom)
    # Harga=Cost, Sisanya=Benefit
    types = ['cost', 'benefit', 'benefit', 'benefit', 'benefit']
    
    # 1. MENENTUKAN NILAI OPTIMAL (X0)
    x0 = []
    for i, col in enumerate(cols):
        if types[i] == 'benefit':
            x0.append(matrix[col].max()) # Max untuk benefit
        else:
            x0.append(matrix[col].min()) # Min untuk cost
            
    # Gabungkan X0 ke dalam matriks utama (Baris paling atas)
    df_calc = matrix.copy()
    df_x0 = pd.DataFrame([x0], columns=cols)
    df_lengkap = pd.concat([df_x0, df_calc], ignore_index=True)
    
    st.write("---")
    st.subheader("2. Matriks Keputusan dengan Nilai Optimal (X0)")
    st.info("Baris 0 adalah Nilai Ideal/Optimal ($X_0$).")
    st.dataframe(df_lengkap)

    # 2. NORMALISASI MATRIKS (R)
    # Rumus ARAS: 
    # Benefit: x / sum(x)
    # Cost: (1/x) / sum(1/x)
    
    df_norm = df_lengkap.copy().astype(float)
    
    for i, col in enumerate(cols):
        if types[i] == 'benefit':
            df_norm[col] = df_lengkap[col] / df_lengkap[col].sum()
        else:
            # Khusus Cost: Ubah jadi 1/x dulu
            reciprocal = 1 / df_lengkap[col]
            df_norm[col] = reciprocal / reciprocal.sum()
            
    with st.expander("Lihat Hasil Normalisasi (Matriks R)"):
        st.dataframe(df_norm)

    # 3. PEMBOBOTAN MATRIKS (D)
    df_weighted = df_norm.copy()
    for i, col in enumerate(cols):
        df_weighted[col] = df_norm[col] * bobot[i]
        
    with st.expander("Lihat Matriks Terbobot (Matriks D)"):
        st.dataframe(df_weighted)

    # 4. NILAI FUNGSI OPTIMALITAS (Si)
    Si = df_weighted.sum(axis=1)
    
    # 5. NILAI DERAJAT UTILITAS (Ki)
    S0 = Si[0] # Nilai Si milik X0 (Baris pertama)
    Ki = Si / S0
    
    # --- HASIL AKHIR ---
    st.write("---")
    st.subheader("🏆 Hasil Akhir & Perangkingan")
    
    # Buat tabel hasil
    final_res = pd.DataFrame({
        'Alternatif': ['OPTIMAL (X0)'] + list(alternatives),
        'Nilai Si (Total)': Si,
        'Nilai Ki (Utilitas)': Ki
    })
    
    # Hapus baris Optimal (X0) dari ranking, kita hanya mau ranking HP nya
    final_ranking = final_res.iloc[1:].copy()
    final_ranking = final_ranking.sort_values(by='Nilai Ki (Utilitas)', ascending=False).reset_index(drop=True)
    
    # Tampilkan Juara
    best_hp = final_ranking.iloc[0]['Alternatif']
    best_score = final_ranking.iloc[0]['Nilai Ki (Utilitas)']
    
    st.success(f"Rekomendasi Terbaik: **{best_hp}** dengan skor **{best_score:.4f}**")
    
    # Tampilkan Tabel
    st.dataframe(final_ranking.style.format({'Nilai Si (Total)': '{:.4f}', 'Nilai Ki (Utilitas)': '{:.4f}'}))
    
    # Visualisasi Bar Chart
    st.bar_chart(final_ranking.set_index('Alternatif')['Nilai Ki (Utilitas)'])
