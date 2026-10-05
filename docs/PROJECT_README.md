# CV Checker Project

Base projet reorganisee pour une livraison propre et exploitable.

## Arborescence
- `src/cv_checker/` : API FastAPI et moteur d analyse CV.
- `src/synthetic_cv_generator/` : generation de CV synthetiques.
- `scripts/powershell/` : scripts de lancement (Windows).
- `scripts/python/` : scripts Python d orchestration.
- `data/cv/` : CV entrants/reels/archives/synthetiques.
- `data/business/` : donnees metier source.
- `data/db/` : bases SQLite.
- `outputs/` : resultats CSV/JSON.
- `docs/` : documentation et references.
- `deliverables/` : livrables de rendu.

## Prerequis
- Python 3.11+
- Dependances Python installees (`requirements.txt`)
- Optionnel OCR: Tesseract + Poppler

## Installation
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancement Rapide
```powershell
# API
./scripts/powershell/lancer_api.ps1

# Traitement incoming -> processed/failed
./scripts/powershell/lancer_reception.ps1

# Generation + test de CV synthetiques
./scripts/powershell/generer_et_tester_synthetiques.ps1 -Count 100 -Seed 20260218
```

## Fichiers utiles
- Guide utilisateur: `docs/GUIDE_UTILISATION_OUTIL_CV.md`
- Organisation: `docs/ORGANISATION_FICHIERS.md`
- Dictionnaire colonnes/warnings: `docs/references/`
