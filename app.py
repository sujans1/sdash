from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).parent
DATA = ROOT / 'data'
EVIDENCE = ROOT / 'evidence'

# Accept files uploaded either in the repository root (as currently arranged
# on GitHub) or in the recommended data/ and evidence/ folders.
def find_file(filename: str, folder: Path) -> Path:
    candidates = (folder / filename, ROOT / filename)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    searched = ', '.join(str(p.relative_to(ROOT)) for p in candidates)
    raise FileNotFoundError(
        f"Required file '{filename}' was not found. Checked: {searched}. "
        f"Upload the file to the repository root or the '{folder.name}/' folder."
    )

BOOK = find_file('Sri_Lanka_Electricity_Actuals_and_CEB_Plan_Combined.xlsx', DATA)
PROJECT_BOOK = find_file('Project_Tables.xlsx', DATA)
APPROVAL_BOOK = find_file('Project_and_PPA_Approvals.xlsx', DATA)
CEB_NCRE_BOOK = find_file('CEB_NCRE_and_Installed_Capacity_v3.xlsx', DATA)
APPLICATION_BOOK = find_file('Renewable_Energy_Applications.xlsx', DATA)

st.set_page_config(page_title='70% by 2030 | Sri Lanka Electricity Reality Check', page_icon='⚡', layout='wide', initial_sidebar_state='expanded')

# Editorial dark theme: designed for an investigative, evidence-led dashboard.
BG = '#0b1117'; PANEL = '#121e28'; LINE = '#263541'; TEXT = '#e8eef2'; MUTED = '#91a3b0'
ACCENT = '#e6b85c'; GREEN = '#55c99a'; BLUE = '#65a9dc'; RED = '#e27d73'; PURPLE = '#b49be8'
st.markdown(f'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:'Manrope',sans-serif}}.stApp{{background:{BG};color:{TEXT}}}
[data-testid="stSidebar"]{{background:#101a23;border-right:1px solid {LINE}}}[data-testid="stSidebar"] *{{color:#dce6eb}}
.block-container{{padding-top:1.2rem;padding-bottom:3rem;max-width:1500px}}
h1,h2,h3{{letter-spacing:-.035em}}h1{{font-size:2.25rem!important;font-weight:800!important}}h2{{font-size:1.4rem!important;font-weight:750!important;margin-top:1rem}}
[data-testid="stMetric"]{{background:{PANEL};border:1px solid {LINE};padding:14px 16px;border-radius:12px}}
[data-testid="stMetricLabel"]{{color:{MUTED}!important}}[data-testid="stMetricValue"]{{color:#f1f5f7!important}}
.kicker{{font-family:'DM Mono',monospace;color:{ACCENT};letter-spacing:.12em;font-size:.72rem;text-transform:uppercase}}
.small-note{{color:{MUTED};font-size:.82rem}}.verdict{{font-size:1.14rem;line-height:1.6;color:#f2f5f7}}
.callout{{background:{PANEL};border:1px solid {LINE};border-left:4px solid {ACCENT};padding:16px 18px;border-radius:10px}}
hr{{border-color:{LINE}}}.stTabs [data-baseweb="tab"]{{font-weight:650}}
a{{color:{BLUE}!important}}
</style>''', unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_all():
    d = {s: pd.read_excel(BOOK, sheet_name=s) for s in pd.ExcelFile(BOOK).sheet_names}
    stage_map = {'Table 1':'Source label: under construction', 'Table 2':'Source label: under development', 'Table 3':'Source label: planning', 'Table 4':'Source label: planning', 'Table 5':'Source label: planning'}
    project_frames=[]
    for sheet in pd.ExcelFile(PROJECT_BOOK).sheet_names:
        x=pd.read_excel(PROJECT_BOOK, sheet_name=sheet)
        x['Zone']=x['Zone'].replace('', pd.NA).ffill()
        x['Source_Table']=sheet
        x['Source_Stage']=stage_map.get(sheet, 'Unclassified')
        project_frames.append(x)
    projects=pd.concat(project_frames, ignore_index=True)
    projects['Capacity (MW)']=pd.to_numeric(projects['Capacity (MW)'], errors='coerce')
    projects['Expected commissioned year']=pd.to_numeric(projects['Expected commissioned year'], errors='coerce')
    projects['Type']=projects['Type'].astype(str).str.replace('Gound','Ground', regex=False)

    a=pd.read_excel(APPROVAL_BOOK, sheet_name='Approved Projects', header=2).dropna(how='all')
    a=a[a['Project Name'].notna() & (a['Project Name'].astype(str).str.lower()!='total capacity')].copy()
    a['Capacity (MW)']=pd.to_numeric(a['Capacity (MW)'], errors='coerce')
    p=pd.read_excel(APPROVAL_BOOK, sheet_name='Table 6 PPA Approvals', header=2).dropna(how='all')
    p=p[p['Project Company'].notna() & (p['Project Company'].astype(str).str.lower()!='total capacity')].copy()
    p['Capacity (MW)']=pd.to_numeric(p['Capacity (MW)'], errors='coerce')

    apps=pd.read_excel(APPLICATION_BOOK, sheet_name=0, header=2).dropna(how='all')
    apps=apps[apps['Application No.'].notna() & (apps['Application No.'].astype(str).str.lower()!='total capacity')].copy()
    apps['Capacity (MW)']=pd.to_numeric(apps['Capacity (MW)'], errors='coerce')

    ncre=pd.read_excel(CEB_NCRE_BOOK, sheet_name='Table 2.2 - NCRE Developments', header=1).dropna(how='all')
    tender=pd.read_excel(CEB_NCRE_BOOK, sheet_name='Table 2.3 - Tendered Projects', header=1).dropna(how='all')
    installed=pd.read_excel(CEB_NCRE_BOOK, sheet_name='Table 1.2 - Installed Capacity', header=1).dropna(how='all')
    q2=pd.read_csv(find_file('PUCSL_Q2_2026_generation.csv', EVIDENCE))
    h1=pd.read_csv(find_file('PUCSL_H1_2026_renewables.csv', EVIDENCE))
    cap26=pd.read_csv(find_file('PUCSL_2026_installed_capacity.csv', EVIDENCE))
    updates=pd.read_csv(find_file('project_updates.csv', EVIDENCE))
    sources=pd.read_csv(find_file('source_register.csv', EVIDENCE))
    legacy_pipeline=pd.read_csv(find_file('CEB_Aug2024_pipeline_snapshot.csv', EVIDENCE))
    legacy_capacity=pd.read_csv(find_file('CEB_Nov2024_installed_capacity.csv', EVIDENCE))
    return d, projects, a, p, apps, ncre, tender, installed, q2, h1, cap26, updates, sources, legacy_pipeline, legacy_capacity

D, projects, approved, ppas, applications, ncre, tenders, ceb_installed_2024, q2, h1, cap26, updates, sources, legacy_pipeline, legacy_capacity = load_all()
totals=D['Actual Generation Totals'].sort_values('Year')
gen=D['Actual Generation Grouped'].sort_values('Year')
cap=D['Actual Capacity Grouped'].sort_values('Year')
peak=D['Actual Peak Demand'].sort_values('Year')
scen=D['CEB Gen Scenarios'].sort_values('Year')
forecast=D['CEB Demand Forecast'].sort_values('Year')
ore=D['CEB ORE Capacity'].sort_values('Year')
