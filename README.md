| Project Akhir Global Positioning System Kelas IF-B |
| Mirza Aditya Mahendra | 123240184 |
| Muhammad Ikhsan Firdaus Saelan | 123240202 |



# 🚌 TransJogja Accessibility Intelligence

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![GeoPandas](https://img.shields.io/badge/GeoPandas-Spatial_Engine-139C5A?style=for-the-badge)
![Folium](https://img.shields.io/badge/Folium-Leaflet_Maps-77B829?style=for-the-badge&logo=leaflet&logoColor=white)

**TransJogja Accessibility Intelligence** adalah aplikasi web berbasis *Location-Based Service* (LBS) dan *Geospatial Intelligence* untuk memantau keterjangkauan halte, mengaudit fasilitas aksesibilitas kursi roda, menganalisis area *blind spot* transportasi publik, serta merencanakan rute perjalanan TransJogja di Daerah Istimewa Yogyakarta (DIY).

---

## ✨ Fitur Utama

### 1. Pelacakan Lokasi & LBS Buffering Real-Time
* **Deteksi GPS Browser Live:** Pembaruan koordinat pengguna otomatis setiap 5 detik menggunakan `streamlit-js-eval` lengkap dengan deteksi otomatis apabila pengguna berada di luar jangkauan layanan DIY (> 25 km dari pusat Yogyakarta).
* **9 Titik Lokasi Preset & Klik Peta Interaktif:** Simulasi cepat dari titik strategis (UPN Veteran Yogyakarta, Malioboro, Tugu Pal Putih, UGM, Stasiun Tugu, Stasiun Lempuyangan, Terminal Giwangan, Plaza Ambarrukmo, dan area *blind spot* Seturan/Babarsari) atau klik langsung pada peta.
* **Dynamic Walking Radius:** Pengaturan radius jarak jalan kaki (`200 m – 1.000 m`) yang memvisualisasikan zona penyangga (*buffer*) secara langsung di peta.

### 2. Audit Aksesibilitas & Indeks Inklusivitas Jaringan
* **Filter Ramah Kursi Roda (`♿`):** Menyaring halte yang memiliki fasilitas *ramp* landai dari total **63 halte** pada **17 koridor aktif** TransJogja.
* **4 Indikator Kinerja Utama (KPI):**
  * **Total Halte:** Ringkasan jumlah halte dan koridor aktif.
  * **Walkable Stops:** Jumlah halte yang dapat dijangkau dalam radius jalan kaki pilihan.
  * **POI Blind Spot:** Proporsi titik strategis Yogyakarta yang berada di luar radius jalan kaki dari halte terdekat.
  * **Indeks Aksesibilitas (%):** Skor komposit berbasis kedekatan halte terdekat, cakupan layanan POI, rasio ketersediaan *ramp*, dan kepadatan halte *walkable*.

### 3. Perencana Rute Tercepat Berbasis Graf Jalan Raya (`🧭 Rute Perjalanan`)
* **Rute Langsung & 1x Transit Otomatis:** Mengevaluasi seluruh koridor langsung maupun kombinasi titik transit (*hub*) untuk menghasilkan satu rekomendasi rute tercepat beserta estimasi jarak dan waktu tempuh.
* **Dijkstra Road-Snapped Slicer:** Mengonversi geometri `rute_transjogja.geojson` menjadi graf jaringan jalan terarah dalam proyeksi meter (`EPSG:32749`) sehingga garis rute 100% mengikuti kelokan jalan raya asli, mematuhi jalur satu arah (seperti *loop* Malioboro–Mataram), dan tidak memotong blok bangunan.
* **Validasi Input:** Penanganan otomatis apabila pengguna memilih halte keberangkatan dan halte tujuan yang sama.

### 4. Analisis Spasial Blind Spot (`📐 Analisis Spasial`)
* Evaluasi jarak layanan terhadap **15 Point of Interest (POI)** utama di Yogyakarta (kampus, stasiun, rumah sakit, pusat perbelanjaan, terminal, dan bandara) untuk mengidentifikasi area yang belum terlayani optimal dalam radius berjalan kaki.

### 5. Pelaporan Kondisi Halte Berbasis Komunitas (`📢 Lapor Kondisi`)
* Pengguna dapat mengirim laporan situasi lapangan (kondisi lancar, antrean padat, armada tiba, atau kendala akses *ramp*) yang tersimpan secara persisten di `laporan_kondisi.json` dan langsung mengubah penanda halte di peta menjadi ikon peringatan merah (`⚠️`).

---

## 📁 Struktur Direktori

```text
transjogja-accessibility/
├── app.py                      # Kode utama aplikasi Streamlit & Spatial Engine
├── halte_transjogja.geojson    # Dataset spasial 63 titik halte & atribut koridor
├── rute_transjogja.geojson     # Dataset spasial 17 jalur koridor TransJogja
├── laporan_kondisi.json        # Penyimpanan laporan kondisi halte (otomatis dibuat)
├── requirements.txt            # Daftar dependensi library Python
└── README.md                   # Dokumentasi proyek
```

---

## ⚙️ Instalasi & Cara Menjalankan

### 1. Prasyarat
Pastikan **Python 3.10 atau versi lebih baru** sudah terpasang di sistem Anda.

### 2. Buat virtual environment di dalam folder proyek

```bash
python -m venv venv
```
### 3. Aktifkan venv

```bash
.\venv\Scripts\activate
```

### 4. Pasang dependensi dan jalankan aplikasi

```bash
pip install -r requirements.txt
streamlit run app.py

```

Aplikasi akan terbuka secara otomatis di browser pada alamat `http://localhost:8501`.

---

## 📐 Metodologi Komputasi Spasial

| Komponen | Metode / Sistem Referensi | Keterangan |
| :--- | :--- | :--- |
| **Sistem Koordinat Metrik** | `EPSG:32749` (WGS 84 / UTM Zone 49S) | Digunakan untuk perhitungan jarak Euclidean akurat dalam satuan meter di wilayah Yogyakarta. |
| **Estimasi Waktu Tempuh** | Jalan kaki: `80 m/menit` (~4,8 km/jam)<br>Bus TransJogja: `367 m/menit` (~22 km/jam) + `4 menit` waktu transit | Disesuaikan dengan kecepatan operasional bus perkotaan dan waktu perpindahan armada di halte hub. |
| **Algoritma Pemotongan Rute** | Graf Jaringan Jalan Terarah + *Dijkstra Shortest Path* | Menyambungkan pecahan segmen `MultiLineString` hanya pada persimpangan sejati (`≤ 25 m`) dan menghubungkan halte cabang melalui graf jalan raya terpadu. |
| **Formula Indeks Aksesibilitas** | $0.35 S_{\text{prox}} + 0.30 S_{\text{poi}} + 0.20 S_{\text{ramp}} + 0.15 S_{\text{density}}$ | Menggabungkan skor kedekatan halte terdekat, cakupan POI non-*blind spot*, persentase halte ber-*ramp*, dan jumlah halte *walkable*. |
