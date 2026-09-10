import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title='SCM Risk & Resilience', page_icon='🛡️', layout='wide')
st.title('🛡️ Supply Chain Risk Management & Resilience Optimization')
st.caption('Risk register • Monte Carlo simulation • multi-sourcing • inventory resilience • recovery • sensitivity analysis')

# ---------------- Sidebar ----------------
st.sidebar.header('Simulation Controls')
seed = st.sidebar.number_input('Random seed', 0, 999999, 42, 1)
n_sim = st.sidebar.slider('Monte Carlo simulations', 1000, 20000, 5000, 1000)
horizon = st.sidebar.slider('Planning horizon (weeks)', 4, 52, 24, 1)

st.sidebar.subheader('Demand & Inventory')
base_demand = st.sidebar.number_input('Weekly demand', 100, 10000, 450, 25)
demand_cv = st.sidebar.slider('Demand variability (CV %)', 0, 50, 15, 1)
initial_inventory = st.sidebar.number_input('Initial inventory', 0, 20000, 600, 50)
holding_cost = st.sidebar.number_input('Holding cost / unit / week', 0.0, 100.0, 2.0, 0.5)
shortage_cost = st.sidebar.number_input('Shortage cost / unit', 0.0, 500.0, 15.0, 1.0)
lost_sales_value = st.sidebar.number_input('Lost-sales value / unit', 0.0, 1000.0, 25.0, 1.0)

st.sidebar.subheader('Primary Supplier')
normal_supply = st.sidebar.number_input('Primary weekly supply', 100, 20000, 500, 25)
supplier_reliability = st.sidebar.slider('Primary reliability %', 50, 100, 92, 1)
supplier_failure_duration = st.sidebar.slider('Disruption duration (weeks)', 1, 12, 3, 1)
disrupted_supply = st.sidebar.number_input('Supply during disruption', 0, 20000, 100, 25)

st.sidebar.subheader('Transportation')
transport_reliability = st.sidebar.slider('Transport reliability %', 50, 100, 90, 1)
transport_capacity_loss = st.sidebar.slider('Transport capacity loss %', 0, 100, 50, 5)
transport_disruption_duration = st.sidebar.slider('Transport disruption duration', 1, 12, 3, 1)

st.sidebar.subheader('Backup Supplier')
use_backup = st.sidebar.checkbox('Enable backup supplier', True)
backup_supply = st.sidebar.number_input('Backup weekly capacity', 0, 20000, 300, 25)
backup_reliability = st.sidebar.slider('Backup reliability %', 50, 100, 95, 1)
backup_cost_multiplier = st.sidebar.number_input('Backup cost multiplier', 1.0, 5.0, 1.5, 0.1)

st.sidebar.subheader('Risk Preference')
lambda_risk = st.sidebar.slider('Risk penalty λ', 0.0, 100.0, 1.0, 0.5)

# ---------------- Risk register ----------------
st.header('1. Supply Chain Risk Register')
default_risks = pd.DataFrame({
    'Risk':['Supplier failure','Transportation disruption','Demand surge','Quality failure','Factory disruption','Raw-material shortage','Cyberattack','Geopolitical disruption','Lead-time variability','Financial distress'],
    'Probability %':[8,12,20,10,7,15,5,8,18,6],
    'Impact 1-10':[10,8,6,8,10,8,10,9,6,7],
    'Exposure 1-10':[9,8,7,6,8,8,7,9,7,6],
    'Vulnerability 1-10':[8,7,6,7,8,7,9,8,6,5]
})
risk_df = st.data_editor(default_risks, use_container_width=True, hide_index=True, key='risk_register')
risk_df['Risk Score'] = risk_df['Probability %']/100 * risk_df['Impact 1-10'] * risk_df['Exposure 1-10'] * risk_df['Vulnerability 1-10']
risk_df['Risk Level'] = pd.cut(risk_df['Risk Score'], [-np.inf,1.5,3.5,6,np.inf], labels=['Low','Moderate','High','Critical'])
cols=st.columns(4)
cols[0].metric('Highest risk score',f"{risk_df['Risk Score'].max():.2f}")
cols[1].metric('Average risk score',f"{risk_df['Risk Score'].mean():.2f}")
cols[2].metric('Critical risks',int((risk_df['Risk Level']=='Critical').sum()))
cols[3].metric('High + Critical',int(risk_df['Risk Level'].isin(['High','Critical']).sum()))
fig=px.bar(risk_df.sort_values('Risk Score'),x='Risk Score',y='Risk',color='Risk Level',orientation='h',title='Risk exposure ranking')
st.plotly_chart(fig,use_container_width=True)
fig=px.scatter(risk_df,x='Probability %',y='Impact 1-10',size='Exposure 1-10',color='Risk Level',hover_name='Risk',title='Probability-impact risk map')
st.plotly_chart(fig,use_container_width=True)

# ---------------- Monte Carlo ----------------
@st.cache_data
def simulate(seed,n_sim,horizon,base_demand,demand_cv,initial_inventory,holding_cost,shortage_cost,lost_sales_value,normal_supply,supplier_reliability,supplier_failure_duration,disrupted_supply,transport_reliability,transport_capacity_loss,transport_disruption_duration,use_backup,backup_supply,backup_reliability,backup_cost_multiplier):
    rng=np.random.default_rng(seed)
    sd=max(1,base_demand*demand_cv/100)
    demand=np.maximum(0,rng.normal(base_demand,sd,(n_sim,horizon))).round().astype(int)
    supplier_bad=rng.random((n_sim,horizon)) >= supplier_reliability/100
    transport_bad=rng.random((n_sim,horizon)) >= transport_reliability/100
    for t in range(horizon):
        if supplier_failure_duration>1 and supplier_bad[:,t].any():
            starts=supplier_bad[:,t].copy()
            for k in range(1,supplier_failure_duration):
                if t+k<horizon: supplier_bad[:,t+k] |= starts
        if transport_disruption_duration>1 and transport_bad[:,t].any():
            starts=transport_bad[:,t].copy()
            for k in range(1,transport_disruption_duration):
                if t+k<horizon: transport_bad[:,t+k] |= starts
    inv=np.full(n_sim,float(initial_inventory)); inventory=np.zeros((n_sim,horizon)); shortage=np.zeros((n_sim,horizon)); supply=np.zeros((n_sim,horizon)); emergency=np.zeros((n_sim,horizon)); holding=np.zeros((n_sim,horizon)); short_cost=np.zeros((n_sim,horizon)); emergency_cost=np.zeros((n_sim,horizon))
    for t in range(horizon):
        p=np.where(supplier_bad[:,t],disrupted_supply,normal_supply)
        p=np.where(transport_bad[:,t],p*(1-transport_capacity_loss/100),p)
        e=np.zeros(n_sim)
        if use_backup:
            ok=rng.random(n_sim)<backup_reliability/100
            e=np.minimum(np.maximum(demand[:,t]-(inv+p),0),np.where(ok,backup_supply,0))
        available=inv+p+e
        s=np.maximum(demand[:,t]-available,0)
        inv=np.maximum(available-demand[:,t],0)
        inventory[:,t]=inv; shortage[:,t]=s; supply[:,t]=p; emergency[:,t]=e
        holding[:,t]=inv*holding_cost
        short_cost[:,t]=s*(shortage_cost+lost_sales_value)
        emergency_cost[:,t]=e*max(0,backup_cost_multiplier-1)*holding_cost*5
    total=holding.sum(1)+short_cost.sum(1)+emergency_cost.sum(1)
    service=1-shortage.sum(1)/np.maximum(demand.sum(1),1)
    return {'demand':demand,'inventory':inventory,'shortage':shortage,'supply':supply,'emergency':emergency,'holding':holding,'short_cost':short_cost,'emergency_cost':emergency_cost,'total':total,'service':service,'supplier_bad':supplier_bad,'transport_bad':transport_bad}

with st.spinner('Running Monte Carlo scenarios...'):
    sim=simulate(seed,n_sim,horizon,base_demand,demand_cv,initial_inventory,holding_cost,shortage_cost,lost_sales_value,normal_supply,supplier_reliability,supplier_failure_duration,disrupted_supply,transport_reliability,transport_capacity_loss,transport_disruption_duration,use_backup,backup_supply,backup_reliability,backup_cost_multiplier)

# ---------------- Dashboard ----------------
st.header('2. Executive Risk Dashboard')
expected_cost=sim['total'].mean(); stockout=(sim['shortage'].sum(1)>0).mean()*100; service=sim['service'].mean()*100; exp_short=sim['shortage'].sum(1).mean(); var95=np.percentile(sim['total'],95); cvar95=sim['total'][sim['total']>=var95].mean()
cols=st.columns(6)
for c,label,val in zip(cols,['Expected cost','Stockout probability','Service level','Expected shortage','95% VaR','95% CVaR'],[f'${expected_cost:,.0f}',f'{stockout:.1f}%',f'{service:.1f}%',f'{exp_short:,.0f}',f'${var95:,.0f}',f'${cvar95:,.0f}']): c.metric(label,val)

# ---------------- Distribution visualizations ----------------
st.header('3. Monte Carlo Risk Distributions')
t1,t2,t3=st.tabs(['Cost','Minimum inventory','Shortage'])
with t1: st.plotly_chart(px.histogram(x=sim['total'],nbins=60,title='Distribution of total simulated cost',labels={'x':'Total cost','y':'Count'}),use_container_width=True)
with t2: st.plotly_chart(px.histogram(x=sim['inventory'].min(1),nbins=50,title='Distribution of minimum inventory',labels={'x':'Minimum inventory','y':'Count'}),use_container_width=True)
with t3: st.plotly_chart(px.histogram(x=sim['shortage'].sum(1),nbins=50,title='Distribution of cumulative shortage',labels={'x':'Shortage units','y':'Count'}),use_container_width=True)

# ---------------- Weekly dynamics ----------------
st.header('4. Supply Chain Dynamics by Week')
week=np.arange(1,horizon+1)
df=pd.DataFrame({'Week':week,'Demand':sim['demand'].mean(0),'Primary supply':sim['supply'].mean(0),'Emergency supply':sim['emergency'].mean(0),'Inventory':sim['inventory'].mean(0),'Shortage':sim['shortage'].mean(0)})
fig=go.Figure()
for col in ['Demand','Primary supply','Emergency supply'] : fig.add_trace(go.Scatter(x=df.Week,y=df[col],mode='lines+markers',name=col))
fig.update_layout(title='Demand versus supply response',xaxis_title='Week',yaxis_title='Units')
st.plotly_chart(fig,use_container_width=True)
fig=go.Figure(); fig.add_trace(go.Scatter(x=df.Week,y=df.Inventory,mode='lines+markers',name='Inventory')); fig.add_trace(go.Scatter(x=df.Week,y=df.Shortage,mode='lines+markers',name='Shortage')); fig.update_layout(title='Inventory and shortage trajectory',xaxis_title='Week',yaxis_title='Units'); st.plotly_chart(fig,use_container_width=True)

# ---------------- Cost ----------------
st.header('5. Cost Decomposition & Tail Risk')
avg_hold=sim['holding'].sum(1).mean(); avg_short=sim['short_cost'].sum(1).mean(); avg_em=sim['emergency_cost'].sum(1).mean()
cost_df=pd.DataFrame({'Component':['Holding','Shortage / lost sales','Emergency sourcing'],'Cost':[avg_hold,avg_short,avg_em]})
st.plotly_chart(px.pie(cost_df,names='Component',values='Cost',title='Expected cost composition'),use_container_width=True)
st.plotly_chart(px.box(pd.DataFrame({'Total simulated cost':sim['total']}),y='Total simulated cost',title='Total-cost tail-risk distribution'),use_container_width=True)

# ---------------- Strategies ----------------
st.header('6. Resilience Strategy Comparison')
strategy_inv=st.slider('Inventory level used for resilience strategies',200,3000,int(initial_inventory),50,key='strategy_inv')
strategies={'Current policy':(initial_inventory,False,1.0),'Higher safety stock':(max(strategy_inv,int(initial_inventory*1.5)),False,1.0),'Dual sourcing':(initial_inventory,True,1.0),'Integrated resilience':(max(strategy_inv,int(initial_inventory*1.5)),True,1.15)}
rows=[]
for name,(start,backup,mult) in strategies.items():
    inv=np.full(n_sim,float(start)); h=np.zeros(n_sim); sc=np.zeros(n_sim); served=np.zeros(n_sim)
    for t in range(horizon):
        p=np.where(sim['supplier_bad'][:,t],disrupted_supply,normal_supply*mult); p=np.where(sim['transport_bad'][:,t],p*(1-transport_capacity_loss/100),p)
        e=np.minimum(np.maximum(sim['demand'][:,t]-inv-p,0),backup_supply) if backup else 0
        avail=inv+p+e; sh=np.maximum(sim['demand'][:,t]-avail,0); served[:,]=served+np.minimum(sim['demand'][:,t],avail); inv=np.maximum(avail-sim['demand'][:,t],0); h+=inv*holding_cost; sc+=sh*(shortage_cost+lost_sales_value)
    total=h+sc
    rows.append({'Strategy':name,'Expected cost':total.mean(),'Stockout probability %':(sc>0).mean()*100,'Service level %':(1-sc/np.maximum(sim['demand'].sum(1),1)).mean()*100,'Expected shortage':(sc/max(shortage_cost+lost_sales_value,1)).mean()})
strategy_df=pd.DataFrame(rows); strategy_df['Risk-adjusted objective']=strategy_df['Expected cost']+lambda_risk*strategy_df['Stockout probability %']
st.dataframe(strategy_df.round(2),use_container_width=True,hide_index=True)
st.plotly_chart(px.bar(strategy_df,x='Strategy',y='Expected cost',title='Expected cost by strategy'),use_container_width=True)
st.plotly_chart(px.bar(strategy_df,x='Strategy',y='Stockout probability %',title='Stockout probability by strategy'),use_container_width=True)
st.plotly_chart(px.scatter(strategy_df,x='Expected cost',y='Service level %',size='Expected shortage',text='Strategy',title='Cost versus resilience trade-off'),use_container_width=True)
best=strategy_df.loc[strategy_df['Risk-adjusted objective'].idxmin(),'Strategy']; st.success(f'Recommended risk-adjusted strategy: **{best}**')

# ---------------- Inventory sensitivity ----------------
st.header('7. Inventory Resilience Sensitivity')
ss_vals=np.arange(max(100,int(initial_inventory*.25)),int(initial_inventory*3)+1,max(25,int(initial_inventory*.1))); ss_rows=[]
for start in ss_vals:
    inv=np.full(n_sim,float(start)); h=np.zeros(n_sim); sc=np.zeros(n_sim)
    for t in range(horizon):
        p=np.where(sim['supplier_bad'][:,t],disrupted_supply,normal_supply); p=np.where(sim['transport_bad'][:,t],p*(1-transport_capacity_loss/100),p); avail=inv+p; sh=np.maximum(sim['demand'][:,t]-avail,0); inv=np.maximum(avail-sim['demand'][:,t],0); h+=inv*holding_cost; sc+=sh*(shortage_cost+lost_sales_value)
    ss_rows.append({'Initial inventory':start,'Expected cost':(h+sc).mean(),'Stockout probability %':(sc>0).mean()*100,'Service level %':(1-sc/np.maximum(sim['demand'].sum(1),1)).mean()*100})
ss=pd.DataFrame(ss_rows)
st.plotly_chart(px.line(ss,x='Initial inventory',y='Expected cost',markers=True,title='Inventory versus expected cost'),use_container_width=True)
st.plotly_chart(px.line(ss,x='Initial inventory',y='Stockout probability %',markers=True,title='Inventory versus stockout probability'),use_container_width=True)
st.plotly_chart(px.scatter(ss,x='Expected cost',y='Service level %',size='Initial inventory',hover_name='Initial inventory',title='Inventory cost-service frontier'),use_container_width=True)
best_inv=ss.loc[ss['Expected cost'].idxmin(),'Initial inventory']; st.info(f'Lowest expected cost in this sensitivity range: **{best_inv:,.0f} units**.')

# ---------------- Supplier concentration ----------------
st.header('8. Supplier Concentration & Diversification')
sup=pd.DataFrame({'Supplier':['A','B','C'],'Procurement share %':[70,20,10],'Reliability %':[92,97,95],'Unit cost':[8.0,9.2,9.5]}); sup['Share fraction']=sup['Procurement share %']/100; hhi=(sup['Share fraction']**2).sum(); st.dataframe(sup,use_container_width=True,hide_index=True); st.metric('Supplier concentration HHI',f'{hhi:.3f}'); st.plotly_chart(px.bar(sup,x='Supplier',y='Procurement share %',title='Supplier dependency'),use_container_width=True)

# ---------------- Disruption frequency ----------------
st.header('9. Disruption Frequency & Recovery')
freq=pd.DataFrame({'Week':week,'Supplier disruption %':sim['supplier_bad'].mean(0)*100,'Transport disruption %':sim['transport_bad'].mean(0)*100}).melt('Week',var_name='Risk',value_name='Probability %'); st.plotly_chart(px.line(freq,x='Week',y='Probability %',color='Risk',markers=True,title='Simulated disruption frequency'),use_container_width=True)
last_short=np.where(sim['shortage']>0,np.arange(1,horizon+1),0).max(1); recovery=np.where(last_short>0,horizon-last_short,0); cols=st.columns(3); cols[0].metric('Average recovery indicator',f'{recovery.mean():.1f} weeks'); cols[1].metric('Median',f'{np.median(recovery):.1f} weeks'); cols[2].metric('90th percentile',f'{np.percentile(recovery,90):.1f} weeks'); st.plotly_chart(px.histogram(x=recovery,nbins=30,title='Recovery indicator distribution',labels={'x':'Weeks remaining after last shortage','y':'Count'}),use_container_width=True)

# ---------------- Disruption sensitivity ----------------
st.header('10. Disruption Probability Sensitivity')
probs=np.arange(.02,.31,.02); pr=[]; rng=np.random.default_rng(seed+1000)
for p in probs:
    costs=[]; flags=[]
    for _ in range(min(1000,n_sim)):
        inv=float(initial_inventory); cost=0; flag=False
        for _t in range(horizon):
            d=max(0,rng.normal(base_demand,max(1,base_demand*demand_cv/100))); bad=rng.random()<p; q=disrupted_supply if bad else normal_supply
            if rng.random()>transport_reliability/100:q*=1-transport_capacity_loss/100
            av=inv+q; sh=max(d-av,0); inv=max(av-d,0); cost+=inv*holding_cost+sh*(shortage_cost+lost_sales_value); flag|=sh>0
        costs.append(cost); flags.append(flag)
    pr.append({'Disruption probability %':p*100,'Expected cost':np.mean(costs),'Stockout probability %':np.mean(flags)*100})
pr=pd.DataFrame(pr); st.plotly_chart(px.line(pr,x='Disruption probability %',y='Expected cost',markers=True,title='Disruption probability versus expected cost'),use_container_width=True); st.plotly_chart(px.line(pr,x='Disruption probability %',y='Stockout probability %',markers=True,title='Disruption probability versus stockout risk'),use_container_width=True)

# ---------------- Scenario table & exports ----------------
st.header('11. Scenario Planning')
scenario=pd.DataFrame({'Scenario':['Normal operation','Supplier disruption','Transportation disruption','Demand surge','Compound disruption'],'Description':['Baseline','Primary supplier unavailable','Transport capacity reduced','Demand increases sharply','Multiple risks simultaneously'],'Recommended response':['Monitor KPIs','Activate alternate sourcing','Reroute / expedite','Use inventory / flexible capacity','Integrated resilience plan']}); st.dataframe(scenario,use_container_width=True,hide_index=True)

st.header('12. Export Results')
st.download_button('Download risk register',risk_df.to_csv(index=False).encode(), 'risk_register.csv','text/csv',key='dl_risk')
st.download_button('Download strategy comparison',strategy_df.to_csv(index=False).encode(), 'strategy_comparison.csv','text/csv',key='dl_strategy')
st.download_button('Download inventory sensitivity',ss.to_csv(index=False).encode(), 'inventory_sensitivity.csv','text/csv',key='dl_inventory')
st.markdown('### Managerial interpretation\n- Do not select a resilience strategy on cost alone.\n- Compare expected cost, service level, stockout probability and tail risk.\n- Diversification reduces dependency but can increase procurement cost.\n- Safety stock protects service but creates holding cost.\n- Compound disruptions should be evaluated because risks can interact.\n- The recommended strategy is the minimum of the illustrative risk-adjusted objective.')
# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Developed by Jaydip Sen | "
    "Supply Chain Risk Management & Resilience Optimization"
)

st.caption(
    "© 2026 Jaydip Sen. All rights reserved. | "
    "For academic, educational, and research purposes."
)