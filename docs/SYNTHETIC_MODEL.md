# Synthetic signal model — AstraLume BioTest Station

**Disclaimer:** Everything in this demo is **synthetic and illustrative**. It is **not** medical, clinical, diagnostic, regulatory, or scientifically validated evidence. Do not present derived metrics as laboratory results.

## Fictional instrument and assay

- Instrument: **AstraLume BioTest Station**
- Assay: antimicrobial efficacy **time-course** (fictional compound vs. synthetic microbial activity)
- Neutral labels only: sample, assay, run, compound, signal
- No real pathogen, drug, patient, or treatment names

## Signal assumptions

| Signal | Behaviour |
|--------|-----------|
| `temperature_c` | Target 37 °C with small Gaussian noise; one scripted excursion near tick 88–95 flagged `quality_flag=review` |
| `ph` | Slow sinusoidal drift bounded to 6.8–7.6 |
| `optical_density` | Logistic growth **or** exponential suppression depending on compound regime |
| `fluorescence_rfu` | Loosely correlated with OD plus noise |
| `dissolved_oxygen_pct` | Slow bounded walk; ~0.5% of rows intentionally missing |
| `reagent_concentration_mg_l` | Slow exponential decay |
| `activity_index` | Weighted demo combination of OD, fluorescence, temperature proximity, and DO, scaled 0–100 |
| `status` | Operational labels only: `normal` / `attention` (demo threshold ≈ 72). Run-level status also includes `paused`, `stopped`, `complete` |

## Determinism and resume

Given `(seed, tick_index)`, readings are reproducible. On API restart, active runs resume from the checkpointed tick so live demos survive mid-edit reloads.

## Planted edge cases (for ETL demos)

1. Missing optional `dissolved_oxygen_pct` (~0.5%)
2. Temperature excursion with `quality_flag=review`
3. One duplicate-looking timestamp row per run (tick 42)
4. Clean transition to `complete` after max runtime

## CSV layout

Each file is one simulated minute (60 second-by-second rows) named:

`AstraLume-BioTest-Station-<test_name_slug>-<device_id>-<UTC_timestamp>.csv`

The human-readable `test_name` is stored in the CSV column and Postgres run record — not relied on as a raw filename.