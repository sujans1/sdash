# Sri Lanka 70% Renewable Electricity by 2030 — Streamlit deployment

## Deploy on Streamlit Community Cloud

1. Upload the **contents** of this folder to the root of your GitHub repository. The repository root must contain `steamliteapp.py`, `requirements.txt`, `data/`, and `evidence/`.
2. In Streamlit Community Cloud, select that repository and set the **Main file path** to `steamliteapp.py`.
3. Deploy. Streamlit Cloud installs the packages listed in the root-level `requirements.txt`.

If your existing app is already connected to GitHub, replace the old app file and `requirements.txt` with these versions, commit, and push. Do not upload only the Python file: the `data/` and `evidence/` folders are required.

## Local run

```bash
pip install -r requirements.txt
streamlit run steamliteapp.py
```

## Important analytical notes

- The 2030 CEB average scenario reports 16,560 GWh renewable generation and 22,997 GWh total scenario generation (about 72.0%).
- The separate CEB demand forecast reports 22,927 GWh net generation. The 70% threshold on that denominator is 16,049 GWh; 16,560 GWh is about 72.2% on this separate basis.
- The historical workbook's 2025 renewable share (60.2%) and PUCSL's 2025 net-generation share (60.7%) use different bases and are not blended.
- 2026 generation evidence is quarterly, not a full-year result.
- Project-register stage labels are retained as supplied; they are not presented as independently verified current statuses.
- Approval, PPA and application registers may overlap and must not be summed as unique capacity.
- Storage MW/MWh is kept distinct from renewable generation GWh.

## Files

- `steamliteapp.py` — deployment entrypoint (same code as `app.py`).
- `requirements.txt` — dependencies installed by Streamlit Cloud.
- `data/` — supplied and combined Excel workbooks.
- `evidence/` — PUCSL, project-update and source-register evidence used by the dashboard.
