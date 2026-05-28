# MarkovLens — User Guide / Buku Manual

> Bilingual guide: English first, then Bahasa Indonesia.
>
> Panduan dwibahasa: bahasa Inggris dulu, lalu bahasa Indonesia.

---

# English

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [First Launch](#first-launch)
4. [Brand Share Forecaster](#brand-share-forecaster)
5. [Customer Churn States](#customer-churn-states)
6. [Generating Reports](#generating-reports)
7. [Glossary](#glossary)
8. [FAQ](#faq)

## Introduction

MarkovLens helps you answer questions like:
- *"What market share will Brand A have in 6 months?"*
- *"How many customers will churn next quarter?"*
- *"If we reduce the at-risk-to-churn transition by 5%, how many customers do we save?"*

It does this using **Markov chain models** — a battle-tested mathematical framework that models how things move between states (e.g., brand A → brand B, or active → at-risk → churned).

You don't need a statistics PhD to use this. The app handles the math; you bring the business question.

## Installation

> *Coming soon: hosted version at [demo.markovlens.app](#)*

For local install:

1. Install [uv](https://docs.astral.sh/uv/) (see [CONTRIBUTING.md](CONTRIBUTING.md))
2. Clone the repo: `git clone https://github.com/afrizzal/markovlens.git`
3. `cd markovlens && uv sync`
4. `uv run streamlit run app/Home.py`
5. Open `http://localhost:8501`

## First Launch

When you first open MarkovLens:

1. **Home screen** — shows 4 KPI cards (Active Models, Domains, Last Forecast Accuracy, Simulations Run This Month) and a sidebar to navigate between modules.
2. **Sample datasets are pre-loaded** — you can immediately explore the two demos without uploading anything.
3. **Try the workflow**: Click "Brand Share" in the sidebar → select sample dataset → click "Run Forecast".

## Brand Share Forecaster

### What it does

Predicts how brand market shares will evolve over time, based on historical consumer brand-switching data.

### Step-by-step

1. **Select a dataset** from the dropdown (sample: "Consumer E-commerce 2024")
2. **Choose a model**:
   - **m1 (Homogeneous)** — best for stable markets
   - **m2 (Time-varying)** — best for dynamic markets where switching patterns change
   - **m3 (Extended)** — best when total market size is growing/shrinking
3. **Set time horizon** — how many months ahead to forecast (1-24)
4. **Click "Run Forecast"**

### Reading the results

- **Stacked area chart** shows historical shares + forecast with confidence bands
- **KPI cards** show market leader, biggest gainer, biggest loser
- **Transition Matrix Explorer** tab — interactive heatmap showing brand-to-brand switching probabilities
- **Monte Carlo Simulator** tab — 10,000 simulated futures with percentile bands

### Pro tip

If a transition matrix cell shows a **warning icon**, it means there were fewer than 20 historical observations for that switch — the probability estimate is noisy. Consider gathering more data or merging sparse states.

## Customer Churn States

### What it does

Models customers as moving between states — Active, At-Risk, Inactive, Churned, Reactivated — and forecasts how many will be in each state over time.

This is more useful than a simple binary "will churn or not?" model because it captures the **journey**.

### Step-by-step

1. **Select a cohort** from the dropdown
2. **Click "Run Analysis"** — Sankey diagram appears showing the flow between states
3. **Use the time scrubber** at the bottom to see how the distribution evolved month-by-month
4. **What-If Simulator** tab — adjust transition probabilities (sliders) to see impact on retention

### Reading the Sankey

- **Thickness of arrows** = number of customers making that transition
- **Node colors** = state (green=Active, amber=At-Risk, red=Churned, etc.)
- **Hover any arrow** to see exact counts

### Business impact

The What-If Simulator gives you the headline metric: *"If you reduce Active→At-Risk by 5%, you save 247 customers and Rp 1.2B over 12 months."*

This is the number you bring to your CFO.

## Generating Reports

1. Click **Reports** in the sidebar
2. Choose a template:
   - **Executive Summary** — 1-page PDF with key metrics
   - **Technical Deep-Dive** — full methodology + appendix
   - **Comparison Report** — m1 vs m2 vs m3 side-by-side
3. Click **Generate PDF** — download starts immediately

Alternative exports:
- **PNG** — individual chart images
- **CSV** — raw forecast data
- **Notebook (.ipynb)** — reproducible Jupyter notebook with all calculations

## Glossary

| Term | Meaning |
|---|---|
| **State** | A category an entity can be in (e.g., a brand, a customer status) |
| **Transition probability** | Chance of moving from state A to state B in one time step |
| **Transition matrix** | Table of all transition probabilities between all states |
| **Markov property** | Future state depends only on current state, not history |
| **Monte Carlo simulation** | Running many random scenarios to estimate a distribution of outcomes |
| **Calibration** | Adjusting raw model probabilities to match real-world observed frequencies |
| **MAPE** | Mean Absolute Percentage Error — accuracy metric (lower = better) |
| **Brier score** | Probabilistic forecast accuracy metric (lower = better) |
| **Walk-forward validation** | Testing the model by re-fitting on historical-only data at each step |

## FAQ

**Q: How much data do I need?**
A: At minimum, 30-60 historical periods and 20+ observations per transition. Less than that and the model is too noisy.

**Q: Can I upload my own dataset?**
A: Yes — go to Settings → Datasets → Upload. CSV format with columns `entity_id`, `period`, `state`.

**Q: Is the math correct?**
A: Yes — based on Chan (2015) IJICIC paper and Becker (2026) Polymarket trade analysis. See [docs/MARKOV-MODELS.md](docs/MARKOV-MODELS.md).

**Q: Can I deploy this myself?**
A: Yes — see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Streamlit Cloud free tier works.

---

# Bahasa Indonesia

## Daftar Isi

1. [Pengenalan](#pengenalan)
2. [Instalasi](#instalasi)
3. [Pertama Kali Menggunakan](#pertama-kali-menggunakan)
4. [Brand Share Forecaster](#brand-share-forecaster-id)
5. [Customer Churn States](#customer-churn-states-id)
6. [Membuat Laporan](#membuat-laporan)
7. [Glosarium](#glosarium)
8. [Tanya Jawab](#tanya-jawab)

## Pengenalan

MarkovLens membantu Anda menjawab pertanyaan seperti:
- *"Berapa market share Brand A 6 bulan lagi?"*
- *"Berapa pelanggan yang akan churn kuartal depan?"*
- *"Kalau kita kurangi transisi at-risk-ke-churn sebesar 5%, berapa pelanggan yang terselamatkan?"*

Aplikasi ini menggunakan **Markov chain models** — kerangka matematika yang sudah terbukti untuk memodelkan perpindahan antar-state (contoh: brand A → brand B, atau aktif → at-risk → churn).

Anda tidak perlu paham statistika tingkat tinggi. Aplikasi menangani matematikanya; Anda fokus ke pertanyaan bisnis.

## Instalasi

> *Akan datang: versi hosted di [demo.markovlens.app](#)*

Untuk instalasi lokal:

1. Install [uv](https://docs.astral.sh/uv/) (lihat [CONTRIBUTING.md](CONTRIBUTING.md))
2. Clone repo: `git clone https://github.com/afrizzal/markovlens.git`
3. `cd markovlens && uv sync`
4. `uv run streamlit run app/Home.py`
5. Buka `http://localhost:8501`

## Pertama Kali Menggunakan

Saat pertama buka MarkovLens:

1. **Layar Home** — menampilkan 4 KPI card (Active Models, Domains, Akurasi Forecast Terakhir, Simulasi Bulan Ini) + sidebar untuk navigasi antar-modul
2. **Dataset contoh sudah dimuat** — Anda bisa langsung eksplorasi dua demo tanpa upload apapun
3. **Coba workflow**: Klik "Brand Share" di sidebar → pilih dataset contoh → klik "Run Forecast"

## Brand Share Forecaster {#brand-share-forecaster-id}

### Fungsi

Memprediksi evolusi market share brand dari waktu ke waktu, berdasarkan data historis perpindahan konsumen antar-brand.

### Langkah-langkah

1. **Pilih dataset** dari dropdown (contoh: "Consumer E-commerce 2024")
2. **Pilih model**:
   - **m1 (Homogeneous)** — terbaik untuk pasar stabil
   - **m2 (Time-varying)** — terbaik untuk pasar dinamis dengan pola perpindahan berubah
   - **m3 (Extended)** — terbaik bila ukuran pasar tumbuh/menyusut
3. **Set time horizon** — berapa bulan ke depan diforecast (1-24)
4. **Klik "Run Forecast"**

### Membaca hasil

- **Stacked area chart** menampilkan share historis + forecast dengan confidence band
- **KPI card** menampilkan market leader, biggest gainer, biggest loser
- **Tab Transition Matrix Explorer** — heatmap interaktif probabilitas perpindahan
- **Tab Monte Carlo Simulator** — 10.000 simulasi masa depan dengan percentile band

### Tips

Bila ada cell transition matrix dengan **ikon warning**, artinya observasi historis < 20 untuk transisi tersebut — estimasi noisy. Tambahkan data atau gabungkan state yang jarang.

## Customer Churn States {#customer-churn-states-id}

### Fungsi

Memodelkan pelanggan sebagai berpindah antar-state — Active, At-Risk, Inactive, Churned, Reactivated — dan memforecast jumlah pelanggan di tiap state seiring waktu.

Ini lebih berguna daripada model biner "akan churn atau tidak?" karena menangkap **perjalanan pelanggan**.

### Langkah-langkah

1. **Pilih cohort** dari dropdown
2. **Klik "Run Analysis"** — Sankey diagram muncul menampilkan flow antar-state
3. **Gunakan time scrubber** di bagian bawah untuk melihat evolusi bulan-per-bulan
4. **Tab What-If Simulator** — sesuaikan probabilitas transisi (slider) untuk lihat dampak ke retention

### Membaca Sankey

- **Ketebalan panah** = jumlah pelanggan yang berpindah
- **Warna node** = state (hijau=Active, amber=At-Risk, merah=Churned, dll.)
- **Hover panah** untuk lihat angka pasti

### Dampak bisnis

What-If Simulator memberikan headline metric: *"Bila Anda kurangi transisi Active→At-Risk sebesar 5%, Anda menyelamatkan 247 pelanggan dan Rp 1,2 M dalam 12 bulan."*

Inilah angka yang Anda bawa ke CFO.

## Membuat Laporan

1. Klik **Reports** di sidebar
2. Pilih template:
   - **Executive Summary** — PDF 1 halaman dengan KPI utama
   - **Technical Deep-Dive** — metodologi lengkap + lampiran
   - **Comparison Report** — m1 vs m2 vs m3 berdampingan
3. Klik **Generate PDF** — download otomatis

Format export alternatif:
- **PNG** — gambar chart individual
- **CSV** — raw forecast data
- **Notebook (.ipynb)** — Jupyter notebook reproducible

## Glosarium

| Istilah | Arti |
|---|---|
| **State** | Kategori sebuah entitas (contoh: brand, status pelanggan) |
| **Transition probability** | Peluang berpindah dari state A ke state B dalam 1 time step |
| **Transition matrix** | Tabel semua probabilitas perpindahan antar-state |
| **Markov property** | State masa depan hanya bergantung pada state sekarang, bukan history |
| **Monte Carlo simulation** | Menjalankan banyak skenario random untuk estimasi distribusi outcome |
| **Calibration** | Menyesuaikan probabilitas mentah model agar match dengan observasi nyata |
| **MAPE** | Mean Absolute Percentage Error — metrik akurasi (kecil = bagus) |
| **Brier score** | Metrik akurasi forecast probabilistik (kecil = bagus) |
| **Walk-forward validation** | Tes model dengan re-fit hanya pakai data historis tiap step |

## Tanya Jawab

**T: Berapa banyak data yang dibutuhkan?**
J: Minimum 30-60 periode historis dan 20+ observasi per transisi. Kurang dari itu, model terlalu noisy.

**T: Bisa upload dataset sendiri?**
J: Bisa — buka Settings → Datasets → Upload. Format CSV dengan kolom `entity_id`, `period`, `state`.

**T: Apakah matematikanya benar?**
J: Ya — berbasis paper Chan (2015) IJICIC dan analisis trade Polymarket Becker (2026). Lihat [docs/MARKOV-MODELS.md](docs/MARKOV-MODELS.md).

**T: Bisa deploy sendiri?**
J: Bisa — lihat [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Streamlit Cloud free tier sudah cukup.
