from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).parent
DATA = ROOT / 'data'
EVIDENCE = ROOT / 'evidence'
BOOK = DATA / 'Sri_Lanka_Electricity_Actuals_and_CEB_Plan_Combined.xlsx'
PROJECT_BOOK = DATA / 'Project_Tables.xlsx'
APPROVAL_BOOK = DATA / 'Project_and_PPA_Approvals.xlsx'
CEB_NCRE_BOOK = DATA / 'CEB_NCRE_and_Installed_Capacity_v3.xlsx'
APPLICATION_BOOK = DATA / 'Renewable_Energy_Applications.xlsx'

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
.small-note{{color:{MUTED};font-size:.82rem}}
[data-testid="stMetricLabel"]{{white-space:normal!important;line-height:1.25!important;font-size:.82rem!important}}
[data-testid="stMetricValue"]{{font-size:clamp(1.25rem,2vw,1.8rem)!important}}
[data-testid="stDataFrame"]{{width:100%}}.verdict{{font-size:1.14rem;line-height:1.6;color:#f2f5f7}}
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
    q2=pd.read_csv(EVIDENCE/'PUCSL_Q2_2026_generation.csv')
    h1=pd.read_csv(EVIDENCE/'PUCSL_H1_2026_renewables.csv')
    cap26=pd.read_csv(EVIDENCE/'PUCSL_2026_installed_capacity.csv')
    updates=pd.read_csv(EVIDENCE/'project_updates.csv')
    sources=pd.read_csv(EVIDENCE/'source_register.csv')
    legacy_pipeline=pd.read_csv(EVIDENCE/'CEB_Aug2024_pipeline_snapshot.csv')
    legacy_capacity=pd.read_csv(EVIDENCE/'CEB_Nov2024_installed_capacity.csv')
    return d, projects, a, p, apps, ncre, tender, installed, q2, h1, cap26, updates, sources, legacy_pipeline, legacy_capacity

D, projects, approved, ppas, applications, ncre, tenders, ceb_installed_2024, q2, h1, cap26, updates, sources, legacy_pipeline, legacy_capacity = load_all()
totals=D['Actual Generation Totals'].sort_values('Year')
gen=D['Actual Generation Grouped'].sort_values('Year')
cap=D['Actual Capacity Grouped'].sort_values('Year')
peak=D['Actual Peak Demand'].sort_values('Year')
scen=D['CEB Gen Scenarios'].sort_values('Year')
forecast=D['CEB Demand Forecast'].sort_values('Year')
ore=D['CEB ORE Capacity'].sort_values('Year')
curt=D['CEB Curtailment'].sort_values('Year')
milestones=D['CEB Milestone Capacity']
additions=D['CEB Annual Additions']

last=totals.iloc[-1]
row30=scen.loc[scen.Year.eq(2030)].iloc[0]
fc30=forecast.loc[forecast.Year.eq(2030)].iloc[0]
renew30=float(row30['Renewables_Avg_RE_GWh'])
ceb_total30=float(row30['Total_Avg_RE_GWh'])
netgen30=float(fc30['Net_Generation_GWh'])
share_scenario=float(row30['Renewable_Share_Avg_RE_pct'])

pages=['The verdict','Generation reality','The 2026 pulse','The 2030 maths','Project delivery tracker','Approvals & applications','Grid readiness','Sources & methodology']
st.sidebar.markdown('<div class="kicker">SRI LANKA / POWER TRANSITION</div>', unsafe_allow_html=True)
st.sidebar.title('70% by 2030')
page=st.sidebar.radio('Investigation', pages, index=0)
st.sidebar.markdown('---')
lo,hi=int(totals.Year.min()),int(totals.Year.max())
years=st.sidebar.slider('Historical years', lo, hi, (lo,hi))
st.sidebar.caption('Historical workbook actuals end in 2025. PUCSL quarterly evidence is shown separately through Q2 2026.')
st.sidebar.markdown('---')
st.sidebar.caption('Evidence cut-off: 13 November 2026')
st.markdown('<div class="kicker">THE NATIONAL ELECTRICITY TRANSITION / INVESTIGATIVE DASHBOARD</div>', unsafe_allow_html=True)
st.title('Can Sri Lanka reach 70% renewable electricity by 2030?')
st.markdown('A delivery reality check: generation, project execution, demand, storage and grid constraints.')
st.markdown('---')

# Reusable plotting helpers.
def style(fig, height=390):
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family='Manrope', color=TEXT), margin=dict(l=24,r=24,t=78,b=28), height=height,
                      legend=dict(orientation='h', y=1.12, x=0, title_text=''))
    fig.update_xaxes(gridcolor=LINE, zerolinecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zerolinecolor=LINE)
    return fig

def section(kicker, heading, note=None):
    st.markdown(f'<div class="kicker">{kicker}</div><h2>{heading}</h2>', unsafe_allow_html=True)
    if note: st.markdown(f'<div class="small-note">{note}</div>', unsafe_allow_html=True)

def source_link(label, url):
    st.markdown(f'[{label}]({url})')

if page=='The verdict':
    section('01 / Executive verdict','Plausible in the CEB plan. Not yet proven in delivery.', 'The latest full-year actual series ends in 2025; 2026 evidence is quarterly and must not be presented as a full-year share.')
    required30=netgen30*0.70
    headroom30=renew30-required30
    st.markdown(f'<div class="callout verdict"><b>Answer:</b> Sri Lanka can technically reach 70% renewable electricity by 2030 under the CEB average generation scenario. But the margin for error is narrow: modelled renewable output of {renew30:,.0f} GWh is only {headroom30:,.0f} GWh ({headroom30/required30:.1%}) above the {required30:,.0f} GWh needed to reach 70% of the separate CEB net-generation forecast. Project delays, weaker hydro conditions, higher demand or grid constraints could erase that margin. The honest verdict is <b>possible, but not yet securely on track.</b></div>', unsafe_allow_html=True)
    st.write('')
    a,b=st.columns(2)
    a.metric('2025 renewable share', '60.7%', 'PUCSL net-generation basis')
    b.metric('CEB 2030 scenario', f'{share_scenario:.1f}%', 'Planning scenario, not actual')
    c,d=st.columns(2)
    c.metric('Renewable generation needed in 2030', f'{required30:,.0f} GWh', '70% of CEB net-generation forecast')
    d.metric('CEB average renewable output', f'{renew30:,.0f} GWh', f'{headroom30:,.0f} GWh above requirement')
    st.caption('PUCSL 2025 actual net generation: 10,966 GWh renewable / 18,054 GWh total = 60.7%. The supplied historical workbook gives 60.2% on a different recorded-generation basis. Both are retained, not blended.')
    st.info('Denominator note: CEB’s 72.0% scenario share uses its 22,997 GWh generation-scenario total. The separate demand forecast reports 22,927 GWh net generation; 70% of that is 16,049 GWh, and 16,560 GWh is about 72.2% on this separate basis.')

    left,right=st.columns([1.25,1])
    with left:
        h=totals[totals.Year.between(*years)]
        f=px.area(h,x='Year',y='Renewable_Share_pct',markers=True,title='Historical renewable share — supplied workbook basis')
        f.add_hline(y=70,line_dash='dash',line_color=ACCENT,annotation_text='70% target')
        f.update_yaxes(title='Share of recorded generation (%)',range=[0,100])
        st.plotly_chart(style(f,390),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    with right:
        x=scen[scen.Year.between(2025,2030)]
        f=px.line(x,x='Year',y='Renewable_Share_Avg_RE_pct',markers=True,title='CEB average renewable generation scenario')
        f.add_hline(y=70,line_dash='dash',line_color=ACCENT,annotation_text='70% target')
        f.update_yaxes(title='Share (%)')
        st.plotly_chart(style(f,390),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    st.caption('The annual 2025–2030 points shown are the year-specific values in the CEB generation-scenario workbook; they are not interpolated between endpoints. They remain planning-scenario values, not observed generation.')
    section('THE THREE TESTS','What must go right','Three conditions determine whether planned capacity becomes dependable renewable electricity.')
    x,y,z=st.columns(3)
    ceb25=float(scen.loc[scen.Year.eq(2025),'Renewables_Avg_RE_GWh'].iloc[0])
    x.metric('Modelled renewable generation growth',f'{renew30/ceb25-1:+.0%}','CEB average scenario, 2025–2030')
    y.metric('Planned renewable capacity in 2030',f'{int(milestones.loc[milestones.Year.eq(2030),"Total_Renewable_MW"].iloc[0]):,} MW','Includes major hydro + other renewables')
    z.metric('CEB-modelled renewable curtailment in 2030',f'{float(curt.loc[curt.Year.eq(2030),"Average_Annual_Curtailment_GWh"].iloc[0]):,.0f} GWh','Planning estimate, not measured actual')
    st.markdown('**The three tests:** (1) **Project delivery** — are projects commissioned on time? (2) **System flexibility** — can transmission, storage and grid operations absorb solar and wind? (3) **Generation reliability** — can hydro conditions and other renewables sustain enough actual output?')
    st.caption('ORE means other renewable energy, principally solar, wind, mini-hydro and biomass in the CEB plan. Capacity announcements are not electricity delivered.')
    source_link('PUCSL Annual Report 2025', 'https://www.pucsl.gov.lk/wp-content/uploads/2026/09/Annual-Report-2025_English.pdf')
    source_link('CEB LTGEP 2025–2044', 'https://ceb.lk/front_img/img_reports/1748839124LTGEP-2025-2044-FINAL_c.pdf')

elif page=='Generation reality':
    section('02 / HISTORICAL EVIDENCE','The renewable share is rising — but it is volatile.', 'Hydro can materially change the annual renewable share. Separate major hydro from non-conventional renewables when interpreting progress.')
    h=totals[totals.Year.between(*years)].copy()
    left,right=st.columns(2)
    with left:
        f=px.line(h,x='Year',y='Renewable_Share_pct',markers=True,title='Renewable share of recorded generation')
        f.add_hline(y=70,line_dash='dash',line_color=ACCENT)
        f.update_yaxes(title='Percent',range=[0,100])
        st.plotly_chart(style(f),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    with right:
        h['Nonrenewable_GWh']=h['Recorded_Total_Generation_GWh']-h['Renewable_Generation_GWh']
        f=px.bar(h,x='Year',y=['Renewable_Generation_GWh','Nonrenewable_GWh'],barmode='stack',title='Annual electricity generation',labels={'Renewable_Generation_GWh':'Renewable generation','Nonrenewable_GWh':'Non-renewable generation','value':'Generation (GWh)'})
        f.update_yaxes(title='GWh')
        st.plotly_chart(style(f),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    f=px.area(gen[gen.Year.between(*years)],x='Year',y='Generation_GWh',color='Source_Group',title='Generation by source — annual actuals',labels={'Generation_GWh':'Generation (GWh)','Source_Group':'Generation source'})
    f.update_yaxes(title='GWh')
    st.plotly_chart(style(f,420),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    f=px.area(cap[cap.Year.between(*years)],x='Year',y='Capacity_MW',color='Source_Group',title='Installed capacity by source — annual actuals',labels={'Capacity_MW':'Installed capacity (MW)','Source_Group':'Capacity source'})
    f.update_yaxes(title='MW')
    st.plotly_chart(style(f,410),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    st.info('MW is rated power capacity; GWh is energy generated. A larger installed MW figure does not guarantee the same increase in annual electricity output. Plant factor, hydrology, outages, dispatch and curtailment all matter.')
    st.markdown('**Accounting caution:** the supplied workbook historical series gives 2025 renewable share of 60.2%. PUCSL reports 2025 net generation of 18,054 GWh, including 6,306 GWh major hydro and 4,660 GWh other renewables: 10,966 GWh or 60.7%. Do not splice the two series without reconciling their definitions.')

elif page=='The 2026 pulse':
    section('03 / LATEST GENERATION','Q2 2026 is a warning against reading capacity as performance.', 'PUCSL Quarterly Renewable Generation Report Q2 2026. Quarter-to-quarter and year-on-year comparisons are shown separately.')
    a,b,c=st.columns(3)
    q2_total=2485.90; q225=2965.0
    a.metric('Renewables generated in Q2 2026',f'{q2_total:,.1f} GWh')
    b.metric('Change vs Q2 2025',f'{(q2_total/q225-1)*100:+.1f}%','Year-on-year')
    c.metric('Q2 2025 generation',f'{q225:,.0f} GWh','Comparable quarter')
    left,right=st.columns(2)
    with left:
        f=px.bar(q2,x='Technology',y=['Q2_2025_GWh','Q2_2026_GWh'],barmode='group',title='Renewable generation by technology: Q2 2025 vs Q2 2026')
        f.update_yaxes(title='GWh')
        st.plotly_chart(style(f,430),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    with right:
        f=px.bar(q2.sort_values('Change_pct'),x='Change_pct',y='Technology',orientation='h',color='Change_pct',color_continuous_scale=['#d66e68','#d6b66d','#55c99a'],title='Year-on-year change by technology')
        f.update_xaxes(title='Change (%)')
        f.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style(f,430),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    st.markdown('**What happened?** Major hydro fell 37% year-on-year and mini-hydro fell 25%. Rooftop solar rose 42% and IPP solar rose 124%, but those gains did not offset the hydro decline. The total renewable generation fall was 16.2%.')
    st.caption('The Q2 2025 technology values in the regulator table are rounded to whole GWh; their sum (2,966 GWh) differs by 1 GWh from the report headline total (2,965 GWh). The percentage comparison uses the published headline totals.')
    st.warning('Source-quality note: the PUCSL report’s Q1-vs-Q2 chart labels and accompanying sentence appear inconsistent (the plotted values imply an increase, while the sentence says a decrease). This dashboard therefore avoids using the quarter-on-quarter comparison. The Q2-vs-Q2 2025 comparison is supported by the technology table and reported total.')
    section('FIRST HALF OF 2026','Renewables still contribute a large energy volume')
    f=px.bar(h1.sort_values('Jan_Jun_2026_GWh',ascending=False),x='Technology',y='Jan_Jun_2026_GWh',color='Technology',title='Cumulative renewable generation, 1 January–30 June 2026')
    f.update_yaxes(title='GWh')
    st.plotly_chart(style(f,390),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    section('CAPACITY SNAPSHOT','Installed renewable capacity at 30 June 2026')
    left,right=st.columns([1,1])
    with left:
        f=px.bar(cap26.sort_values('Capacity_MW'),x='Capacity_MW',y='Technology',orientation='h',title='PUCSL installed renewable capacity by technology')
        f.update_xaxes(title='MW')
        st.plotly_chart(style(f,410),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    with right:
        st.metric('Renewable capacity reported by PUCSL',f'{cap26.Capacity_MW.sum():,.0f} MW','Includes major hydro + NCRE')
        st.markdown('The Q2 report lists 1,527 MW major hydro and approximately 3,675 MW NCRE. Rooftop solar is a substantial component. Capacity is a stock measure; quarterly GWh is an output measure.')
        st.warning('PUCSL notes that rooftop solar, some self-consumption and non-telemetered mini-hydro contributions are estimated/modelled in generation profiles. Treat these figures as regulator-reported series, not all directly metered plant output.')
    source_link('Open PUCSL Q2 2026 Renewable Generation Report (PDF)', 'https://www.pucsl.gov.lk/wp-content/uploads/2026/10/Renewable-Generation-Report-Q2-2026_Final.pdf')

elif page=='The 2030 maths':
    section('04 / THE CENTRAL TEST','The target has a narrow modelled cushion.', 'Test the renewable GWh required as demand changes and the share of CEB-planned renewable generation that actually arrives.')
    a,b,c=st.columns(3)
    with a: denominator=st.number_input('2030 net generation (GWh)',min_value=5000,max_value=60000,value=int(netgen30),step=100)
    with b: target=st.slider('Renewable target (%)',50,90,70)
    with c: delivery=st.slider('CEB renewable output delivered (%)',60,110,100)
    required=denominator*target/100
    delivered=renew30*delivery/100
    implied=delivered/denominator*100
    cushion=delivered-required
    a,b,c=st.columns(3)
    a.metric('Renewable generation required',f'{required:,.0f} GWh')
    b.metric('Scenario renewable output delivered',f'{delivered:,.0f} GWh')
    c.metric('Implied renewable share',f'{implied:.1f}%',f'{implied-target:+.1f} percentage points',delta_color='normal' if implied>=target else 'inverse')
    st.metric('Surplus / shortfall against target',f'{cushion:+,.0f} GWh','Above requirement' if cushion>=0 else 'Below requirement',delta_color='normal' if cushion>=0 else 'inverse')
    f=go.Figure()
    f.add_trace(go.Bar(x=['Required for target','CEB average scenario output','Output at selected delivery rate'],y=[required,renew30,delivered],marker_color=[ACCENT,BLUE,GREEN]))
    f.update_layout(title='2030 renewable electricity: requirement vs scenario',yaxis_title='GWh')
    st.plotly_chart(style(f,370),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    st.markdown('**Break-even delivery:** the 2030 CEB average renewable generation scenario is 16,560 GWh. At the CEB demand forecast net generation of 22,927 GWh, 70% requires 16,049 GWh. Sri Lanka therefore needs to deliver about **96.9% of the CEB average renewable output assumption** if total generation stays at that level.')
    scenarios=[]
    for pct in [100,97,95,90,85,80]:
        out=renew30*pct/100
        scenarios.append({'CEB renewable output delivered':f'{pct}%','Renewable output (GWh)':round(out),'Implied share (%)':round(out/denominator*100,1),'Target result':'Meets' if out>=required else 'Misses'})
    st.dataframe(pd.DataFrame(scenarios),use_container_width=True,hide_index=True)
    st.warning('This is a transparent sensitivity test, not a dispatch model. It holds the generation denominator fixed and scales CEB average renewable output. It does not independently simulate hydrology, plant factors, hourly dispatch, commissioning schedules, curtailment or demand response.')
    st.markdown('**Denominator reconciliation:** CEB generation-scenario total for 2030 is 22,997 GWh, while the CEB demand forecast sheet reports 22,927 GWh net generation. CEB reports approximately 72.0% using its own generation scenario denominator; using the demand forecast denominator gives approximately 72.2%. Both figures are preserved here.')

elif page=='Project delivery tracker':
    section('05 / PROJECT DELIVERY','The pipeline is not the same thing as committed or operational capacity.', 'The 27-project register is preserved as supplied. Source-table stage labels are not independently verified project statuses.')
    total_mw=projects['Capacity (MW)'].sum()
    a,b,c=st.columns(3)
    a.metric('Projects in Project_Tables.xlsx',f'{len(projects)}')
    b.metric('Listed pipeline capacity',f'{total_mw:,.0f} MW')
    c.metric('Capacity in source planning tables',f'{projects.loc[projects.Source_Stage.str.contains("planning",case=False),'Capacity (MW)'].sum():,.0f} MW')
    st.markdown('**Source-table grouping:** Table 1 = under construction; Table 2 = under development; Tables 3–5 = planning. These are the workbook’s labels and should not be mistaken for current independent verification.')
    stages=sorted(projects.Source_Stage.unique())
    chosen=st.multiselect('Filter by source-table stage',stages,default=stages)
    pview=projects[projects.Source_Stage.isin(chosen)].copy()
    stage_labels={'Source label: under construction':'Under construction','Source label: under development':'Under development','Source label: planning':'Planning'}
    pview['Stage for chart']=pview['Source_Stage'].map(stage_labels).fillna(pview['Source_Stage'])
    f=px.bar(pview.groupby(['Source_Table','Stage for chart'],as_index=False)['Capacity (MW)'].sum(),x='Source_Table',y='Capacity (MW)',color='Stage for chart',title='Listed capacity by source table')
    f.update_yaxes(title='MW')
    st.plotly_chart(style(f,340),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    # Add latest known evidence as an additional column only for clearly matched identities.
    latest_map={
        'siyabalaanduwa':'Siyabalanduwa / Rividhanavi solar',
        'mannar (phase 1)':'Mannar Phase 1 / Nadukkuda wind',
        'mullikulam i & ii':'Mullikulam I & II wind'
    }
    status_by_project={}
    for key, name in latest_map.items():
        r=updates[updates.Project.eq(name)]
        if not r.empty: status_by_project[key]=r.iloc[0]
    def matched_update(name):
        n=str(name).strip().lower()
        for key,r in status_by_project.items():
            if key in n:
                return r
        return None
    pview['Latest evidence status']=pview['Project Name'].apply(lambda n: matched_update(n)['Latest_verified_status'] if matched_update(n) is not None else 'No newer project-specific status verified in this build')
    pview['Latest expected completion']=pview['Project Name'].apply(lambda n: matched_update(n)['Latest_expected_completion'] if matched_update(n) is not None else 'Not independently updated')
    st.dataframe(pview[['Project Name','Type','Capacity (MW)','Zone','Expected commissioned year','Source_Stage','Latest evidence status','Latest expected completion']],use_container_width=True,hide_index=True)
    st.download_button('Download filtered 27-project register (CSV)',pview.to_csv(index=False).encode('utf-8'),'27_project_pipeline.csv','text/csv')
    section('VERIFIED PROJECT UPDATES','What has moved beyond the workbook snapshot')
    st.dataframe(updates[['Project','Capacity_MW','Previous_status','Latest_verified_status','Latest_expected_completion','Evidence_date','Source_type','Confidence','Source_URL']],use_container_width=True,hide_index=True,column_config={'Source_URL':st.column_config.LinkColumn('Evidence link')})
    st.caption('Only projects with sufficiently specific, recent evidence are shown as updated. Absence of an update does not mean a project has stopped; it means a new milestone was not verified in this research pass.')
    section('ADDITIONAL COMMISSIONED CAPACITY','Keep outside the 27-project total')
    st.markdown('''- **Ranna solar — 10 MW:** connected and synchronized to the grid on 23 September 2026; ceremonial commissioning on 20 October 2026. This project is not one of the 27 listed rows.
- **Diya Janani floating solar — 5 MW:** WindForce reported commissioning in September 2026. It also appears in your applications register; identity should be reconciled using its licence/application number before treating records as separate projects.
- **Safe Power International wind — 10 MW:** WindForce reported civil construction commenced, with a revised May 2027 schedule following a force-majeure extension after Cyclone Ditwah. This is outside the 27-project list.''')
    source_link('CSE / Vidullanka Ranna commissioning announcement','https://cdn.cse.lk/cmt/announcement_portal_prod/DPV%20-%20CSE%20Announcement_20261020_0001_15351580915509941.pdf')

elif page=='Approvals & applications':
    section('06 / DEVELOPMENT PIPELINE','Separate the stages. Never add overlapping registers together.', 'Approvals, PPAs and applications are separate datasets. They can refer to the same physical project and should not be summed into a single national capacity number.')
    tab1,tab2,tab3,tab4=st.tabs(['Approved projects','PPA approval records','Applications','CEB tender snapshot'])
    with tab1:
        st.metric('Listed approved-project capacity',f'{approved["Capacity (MW)"].sum():,.0f} MW')
        st.dataframe(approved,use_container_width=True,hide_index=True)
        st.caption('Approval year and proposed commissioning year are reproduced from your workbook. Approval does not mean construction or commissioning.')
    with tab2:
        st.metric('Capacity in PPA approval records',f'{ppas["Capacity (MW)"].sum():,.0f} MW')
        st.dataframe(ppas,use_container_width=True,hide_index=True)
        st.caption('These are approval records, not proof every PPA has been executed. GSS and bid tariff fields are reproduced as supplied; tariff currency/unit labels require source-document context before comparisons.')
    with tab3:
        st.metric('Application records',f'{len(applications)}')
        st.metric('Capacity across application rows',f'{applications["Capacity (MW)"].sum():,.1f} MW')
        st.dataframe(applications,use_container_width=True,hide_index=True)
        st.warning('Application rows do not show their subsequent regulatory outcome. One listed facility, Diya Janani at Dambuluoya, is separately reported as commissioned in September 2026. Verify project identity against the licence register before deduplicating.')
    with tab4:
        st.markdown('**CEB NCRE pipeline snapshot — August 2024.** This is a historical snapshot and must not be described as the current pipeline.')
        st.dataframe(legacy_pipeline,use_container_width=True,hide_index=True)
        st.markdown('**CEB installed capacity snapshot — end-November 2024.** Values are from the CEB workbook; blanks and category totals are not inferred.')
        st.dataframe(legacy_capacity,use_container_width=True,hide_index=True)
        st.markdown('**NCRE development snapshot**')
        st.dataframe(ncre,use_container_width=True,hide_index=True)
        st.caption('The source workbook repeats this NCRE developments table in a second worksheet; the duplicate is intentionally not counted twice.')
        st.markdown('**Tendered project register**')
        st.dataframe(tenders,use_container_width=True,hide_index=True)
        st.caption('The tender table contains milestones such as LOIs, PPAs signed, under construction and commissioned, but the workbook does not provide a reliable current update date for every row. Use it as a dated historical source, not a live status list.')
    section('WHY THE REGISTERS CANNOT BE ADDED','A project can appear in several workbooks as it moves through approvals, PPA, construction and operation.')
    st.markdown('For example, Mullikulam appears in the 27-project pipeline and the approved-project workbook. Mannar wind names appear in project and PPA records. The application workbook may contain a project that later reached commissioning. A credible tracker needs a stable project ID, site, developer and capacity—not just matching text names.')

elif page=='Grid readiness':
    section('07 / GRID READINESS','New generation only helps if the system can absorb and deliver it.', 'CEB LTGEP values are projections. PUCSL Q2 2026 evidence provides a more recent view of renewable output and the system profile.')
    a,b,c=st.columns(3)
    r2030=milestones[milestones.Year.eq(2030)].iloc[0]
    a.metric('CEB storage milestone 2030',f'{int(r2030.Energy_Storage_MW):,} MW')
    b.metric('CEB storage milestone 2035',f'{int(milestones.loc[milestones.Year.eq(2035),"Energy_Storage_MW"].iloc[0]):,} MW')
    c.metric('CEB 2030 renewable curtailment',f'{float(curt.loc[curt.Year.eq(2030),"Average_Annual_Curtailment_GWh"].iloc[0]):,.0f} GWh')
    left,right=st.columns(2)
    with left:
        f=px.line(ore,x='Year',y=['Solar_Cumulative_MW','Wind_Cumulative_MW','Mini_Hydro_Cumulative_MW','Biomass_Cumulative_MW'],markers=True,title='CEB planned cumulative ORE capacity')
        f.update_yaxes(title='MW')
        st.plotly_chart(style(f),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    with right:
        f=px.bar(additions,x='Year',y=['ORE_MW','BESS_MW','PSPP_MW'],title='CEB annual additions: ORE and storage')
        f.update_yaxes(title='MW')
        st.plotly_chart(style(f),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    section('CURTAILMENT','The CEB plan already assumes renewable energy will be curtailed')
    f=go.Figure()
    f.add_trace(go.Bar(x=curt.Year,y=curt.Average_Annual_Curtailment_GWh,name='Average annual curtailment'))
    f.add_trace(go.Scatter(x=curt.Year,y=curt.Curtailment_pct_Total_Generation,name='Share of total generation',yaxis='y2',mode='lines+markers'))
    f.update_layout(title='CEB projected renewable curtailment',yaxis=dict(title='GWh'),yaxis2=dict(title='% of total generation',overlaying='y',side='right'))
    st.plotly_chart(style(f,400),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    section('DEMAND',"2025 peak demand exceeded CEB’s forecast",'A one-year actual-versus-forecast comparison; it does not by itself establish a multi-year trend.')
    left,right=st.columns(2)
    with left:
        f=px.line(peak,x='Year',y=['Day_Max_Demand_MW','Night_Max_Demand_MW'],markers=True,title='Actual day and night maximum demand')
        f.update_yaxes(title='MW')
        st.plotly_chart(style(f),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    with right:
        f=px.line(forecast,x='Year',y=['Day_Peak_MW','Night_Peak_MW'],markers=True,title='CEB forecast day and night peak')
        f.update_yaxes(title='MW')
        st.plotly_chart(style(f),use_container_width=True, config={'displayModeBar':False,'responsive':True})
    p25=peak[peak.Year.eq(2025)].iloc[0]; fc25=forecast[forecast.Year.eq(2025)].iloc[0]
    st.markdown(f"2025 actual day peak was **{p25.Day_Max_Demand_MW:,.0f} MW** versus CEB's forecast **{fc25.Day_Peak_MW:,.0f} MW**; actual night peak was **{p25.Night_Max_Demand_MW:,.0f} MW** versus forecast **{fc25.Night_Peak_MW:,.0f} MW**. Demand forecasting and firm capacity matter alongside annual renewable GWh.")
    section('STORAGE IS NOT GENERATION','Track MW and MWh separately')
    st.markdown('WindForce reported five standalone BESS sites commissioned by October 2026, totalling **50 MW / 200 MWh**, within a 13-site portfolio of **130 MW / 520 MWh**. This is storage power and energy capacity, not renewable generation capacity. Storage can shift and balance energy; it does not create renewable GWh.')
    st.warning('Observed curtailment cost: WindForce reported LKR 193.57 million in foregone revenue due to curtailment during the six months ended 30 September 2026. The company said the compensation framework had been approved, but discussions continued and the timing/recovery remained uncertain. This is one company’s reported impact, not a national total.')
    source_link('WindForce interim statement filed with CSE (11 Nov 2026)','https://cdn.cse.lk/cmt/upload_report_file/2173_1794389718509.pdf')
    source_link('Daily FT: WindForce first-half update (12 Nov 2026)','https://www.ft.lk/business/x/34-799966')

else:
    section('08 / SOURCES & METHODOLOGY','An evidence trail, not a black box.')
    st.markdown('### Source hierarchy')
    st.markdown('1. Official regulator, CEB, Ministry, SLSEA, Gazette, Cabinet and CSE disclosures.\n2. Project developer and lender disclosures.\n3. Credible Sri Lankan business press when primary evidence is unavailable; labelled secondary.')
    st.dataframe(sources,use_container_width=True,hide_index=True,column_config={'URL':st.column_config.LinkColumn('Open source',display_text='Open source')})
    st.caption('Check each source’s publication or reporting date before relying on a project status. A source link is provided for direct verification.')
    st.markdown('### Data definitions and caveats')
    notes=[
        ('Historical generation','The supplied combined workbook provides annual source-level generation through 2025. Its recorded renewable share is calculated from major hydro plus recorded NCRE categories. Source classification may change over the long historical period.'),
        ('PUCSL 2025 net-generation basis','PUCSL Annual Report 2025 reports 18,054 GWh net generation, comprising 6,306 GWh major hydro and 4,660 GWh other renewables. Total renewable net generation is 10,966 GWh, or 60.7%. This is not identical to the supplied workbook’s 60.2% recorded-generation basis.'),
        ('PUCSL Q2 2026','Q2 renewable generation was 2,485.9 GWh, 16.2% below Q2 2025 (2,965 GWh). Major hydro fell 37%, mini hydro 25%, rooftop solar rose 42% and IPP solar rose 124%. Do not interpret a quarterly decline as a full-year renewable-share outcome.'),
        ('CEB LTGEP','The CEB 2030 average renewable generation scenario is 16,560 GWh and scenario total generation 22,997 GWh (about 72.0%). CEB demand forecast net generation is 22,927 GWh. Using this denominator gives about 72.2%. Future values are planning assumptions, not guarantees.'),
        ('27-project pipeline','27 rows / 2,756 MW across five project tables. The table grouping labels are retained as supplied: Table 1 under construction, Table 2 under development, Tables 3–5 planning. The labels are not current verified status for every project.'),
        ('Approvals and PPA records','Approval and PPA capacity totals are not added to the 27-project pipeline because project overlap is likely. No stable project identifier was supplied.'),
        ('Applications','Five application rows totalling 15.6 MW. An application is not an approval, PPA, construction milestone or commissioning event.'),
        ('CEB NCRE workbook','Contains an installed-capacity snapshot dated November 2024, pipeline totals dated August 2024, NCRE progress notes and tendered-project progress. The duplicate NCRE developments sheet is not double-counted.'),
        ('Curtailment and storage','CEB curtailment and storage figures are plan values. The dashboard keeps MW, MWh and GWh distinct. BESS MW/MWh are not counted as renewable generation capacity.'),
        ('Project status evidence','Latest verified updates are a limited evidence sample, not a complete independent audit of all 27 projects. No update shown means no newer project-specific milestone was verified in this build—not that the project is inactive.')]
    for head,body in notes:
        with st.expander(head): st.write(body)
    st.markdown('### Important calculations')
    st.code('Renewable share (%) = (renewable generation (GWh) / total generation (GWh)) × 100\n70% threshold (GWh) = forecast total generation (GWh) × 0.70\nGeneration headroom (GWh) = expected renewable generation − 70% threshold\nProject pipeline MW ≠ commissioned MW ≠ annual renewable generation GWh')
    st.info('The 2030 feasibility calculator uses the separate CEB net-generation forecast as its denominator. The CEB scenario percentage is displayed on the scenario’s own total-generation denominator. These bases are not silently mixed.')
    st.markdown('### Files bundled')
    for name in ['Sri_Lanka_Electricity_Actuals_and_CEB_Plan_Combined.xlsx','Project_Tables.xlsx','Project_and_PPA_Approvals.xlsx','Renewable_Energy_Applications.xlsx','CEB_NCRE_and_Installed_Capacity_v3.xlsx','ceb new.xlsx']:
        st.write('• '+name)

st.markdown('---')
st.markdown('<div class="small-note">Sri Lanka 70% renewable electricity by 2030 · Evidence cut-off 13 Nov 2026 · Historical actuals, quarterly regulator evidence and planning scenarios are deliberately separated. Prepared with Streamlit + Plotly.</div>',unsafe_allow_html=True)
