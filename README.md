# 📄 CV Checker — automated CV screening for Grandir

> Read incoming PDF CVs, extract candidate information, score them against job profiles and flag what a recruiter must double-check.

**Company project (GOAL programme) with Grandir · February 2026**

> No CV, business data or output is versioned — test it with the synthetic CV generator.

---

## What it does
```
data/cv/incoming/*.pdf ─► text extraction (+ OCR fallback: Tesseract/Poppler)
                       ─► candidate parsing (identity, education, experience, skills…)
                       ─► job scoring against job profiles
                       ─► batch_results.csv / .json  +  warnings column
                       ─► PDFs archived to processed/ or failed/
```

- **FastAPI** endpoint for single-CV analysis + a **batch mode** for daily use (history of every run kept for audit).
- **Job-profile scoring** engine and a documented dictionary of output columns and warnings.
- **Synthetic CV generator** to test changes on hundreds of realistic, fake CVs before touching real data — reproducible with a seed.
- Windows-friendly operations: one PowerShell script per task (API, reception, synthetic test run).

## Run it (Windows)
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
./scripts/powershell/generer_et_tester_synthetiques.ps1 -Count 100 -Seed 20260218   # fake CVs + batch test
./scripts/powershell/lancer_api.ps1                                               # FastAPI
```
User guide: [`docs/GUIDE_UTILISATION_OUTIL_CV.md`](docs/GUIDE_UTILISATION_OUTIL_CV.md) · output columns & warnings: [`docs/references/`](docs/references)

## Stack
`Python 3.11` `FastAPI` `PDF parsing` `Tesseract OCR` `Poppler` `SQLite` `pandas` `PowerShell`

---

### 🇫🇷 En bref
Outil de présélection de CV pour Grandir (fév. 2026) : lecture de CV PDF (avec OCR si besoin), extraction des informations candidat, score par rapport à des fiches métier, alertes à vérifier, API FastAPI, traitement par lots et générateur de CV synthétiques pour tester sans données réelles. Aucun CV ni donnée publiés : test avec le générateur de CV synthétiques.
