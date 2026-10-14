# Predicting how long a jet engine will last (RUL)

**In one sentence:** a small model looks at sensor readings from a jet engine and estimates how many more flights ("cycles") it can do before it fails.

Project page (charts, plain language): `docs/index.html`. It is served with GitHub Pages once Pages is enabled for the `/docs` folder.

## The question

Can sensor data tell us how much life an engine has left, so that maintenance can be planned instead of reacting to a failure?

## Who could benefit, and how

This is a learning project on simulated data, so it does not serve anyone yet. In principle, maintenance planners at airlines or engine service companies could use a model like this to decide when to inspect an engine (plausible, not tested here).

## Data and licence

- NASA C-MAPSS turbofan simulation, subset FD001: 100 training engines run to failure (20,631 rows), 100 test engines that stop early, plus the true remaining life of each test engine.
- Source: NASA Prognostics Center of Excellence data repository. Cite: Saxena, A. and Goebel, K. (2008), *Turbofan Engine Degradation Simulation Data Set*. Public for research use. Check the repository terms before reuse.
- The three files are in `data/`.

## How it works

1. For each training engine, count backwards from its last cycle to get "cycles left" for every row.
2. Remove 8 columns that never change, scale the rest to 0 to 1.
3. Train an XGBoost regression model (a set of 100 small decision trees) to predict cycles left.
4. Score it on engines it has not seen. How you do this scoring matters a lot (see results).

## Results

All numbers come from `python src/rul_evaluation.py` and are saved in `reports/results.json`. RMSE and MAE are in cycles, lower is better.

| Model | Tested how | RMSE | MAE |
|---|---|---|---|
| XGBoost, original notebook | Random 80/20 row split | 35.82 | 25.52 |
| XGBoost, same model | 5-fold CV, whole engines held out | 38.15 | 26.89 |
| Mean predictor | Official test set, 100 engines | 52.62 | 40.88 |
| Linear regression | Official test set | 31.25 | 25.98 |
| XGBoost (original settings) | Official test set | 25.95 | 19.14 |
| XGBoost, labels capped at 125 | Official test set | **18.93** | 14.43 |

Over five random seeds (with row and column subsampling) the capped model has an RMSE of 18.84 on average, standard deviation 0.39.
More rows (the no-`cycle` variant, linear baselines) are in `reports/results.json`.

**What this means:** the original score of 35.82 is real, but the random split puts rows of the same engine into both train and test. With whole engines held out, the same model scores 38.15. The official test looks at one reading per engine (the last one), which is easier, so its numbers are lower and cannot be compared directly with the first two.

## Limitations

- Simulated data, one fault type, one operating condition.
- The `cycle` column is the most important feature (48 percent of importance). Without it the official-test RMSE rises from 25.95 to 33.57.
- Capping labels at 125 was compared on the same 100 test engines used for the final score, so 18.93 is probably a little optimistic.
- No uncertainty estimate, no test on the other C-MAPSS subsets.

## How to run

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/rul_evaluation.py    # writes reports/results.json and docs/data.js
```

The original exploration notebook is `notebooks/01_EDA.ipynb`. Open `docs/index.html` in a browser to see the page.

## What is coursework and what I extended

- Original work (kept): the exploration notebook and the first XGBoost model, with the 35.82 and 25.52 scores.
- Extended later: the evaluation script with baselines, grouped split, official test set and seed check, plus the static page. The Streamlit dashboard was moved to `_archive/` because the project now uses static pages only.

## For technical readers

- Target: `RUL = max_cycle - cycle` per engine. Alternative target: `min(RUL, 125)`.
- Features: 17 columns (`cycle`, `op1`, `op2`, 14 sensors) after dropping `op3`, `s1`, `s5`, `s6`, `s10`, `s16`, `s18`, `s19`. The MinMax scaler is fit on the training folds only (in the original random-split notebook it was fit on all rows).
- Model: `XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)`.
- Grouped CV: `GroupKFold(5)` with `unit` as group.
- Official test: last cycle of each test engine against `RUL_FD001.txt`.
- Versions are pinned in `requirements.txt` (Python 3.11).

## Repository layout

```
data/        NASA FD001 files
notebooks/   01_EDA.ipynb (original)
src/         rul_evaluation.py
reports/     results.json
docs/        static project page (index.html, data.js, style.css)
_archive/    moved files: old Streamlit app, dev container, notebook checkpoints, original README
```

Smrity Mallik, MSc AI and Data Science (Gisma, Berlin), B.Eng. Mechanical Engineering.
GitHub: github.com/malliksmrity. LinkedIn: linkedin.com/in/smritymallik.

## Process and automation

- `PROCESS.md`: backlog, definition of done and sprint rhythm for the next work (a plan, not past experience).
- `.github/workflows/ci.yml`: GitHub Actions check (written here, not yet run on GitHub).
- `Dockerfile`: container for the main script (not built or tested yet).
