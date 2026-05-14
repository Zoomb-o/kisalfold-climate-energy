import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xgboost as xgb

df = pd.read_csv('data/processed/master_dataset.csv')
df['date'] = pd.to_datetime(df['date'])
df['temp_squared']   = df['temp_mean_c'] ** 2
df['day_of_year']    = df['date'].dt.dayofyear
df['year_trend']     = df['date'].dt.year - 2015
df['temp_x_weekend'] = df['temp_mean_c'] * df['is_weekend']
df = df.sort_values('date')
df['temp_roll7'] = df['temp_mean_c'].rolling(7, min_periods=1).mean()

FEATURES = [
    'temp_mean_c','temp_max_c','temp_min_c',
    'temp_squared','temp_roll7','HDD','CDD',
    'wind_mean_m_s','solar_rad_j_m2','precip_mm',
    'month','weekday','is_weekend',
    'day_of_year','year_trend','temp_x_weekend',
]

train = df[df['date'] <= '2021-12-31']
model = xgb.XGBRegressor(
    n_estimators=1000, learning_rate=0.03, max_depth=5,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
    random_state=42, verbosity=0,
)
model.fit(train[FEATURES], train['load_mean_MW'], verbose=False)
print('Model trained')

proj = pd.read_csv('data/processed/cmip6_projections.csv')
hist = pd.read_csv('data/processed/era5_daily.csv')
hist['date'] = pd.to_datetime(hist['date'])
hist['month'] = hist['date'].dt.month

monthly_stats = hist.groupby('month').agg(
    spread=('temp_mean_c', lambda x: x.max() - x.min()),
    wind=('wind_mean_m_s','mean'),
    solar=('solar_rad_j_m2','mean'),
    precip=('precip_mm','mean'),
).reset_index()

records = []
for scenario in proj['scenario'].unique():
    s = proj[proj['scenario'] == scenario]
    for year in sorted(s['year'].unique()):
        yr = s[s['year'] == year].copy()
        yr = yr.merge(monthly_stats, on='month')
        yr['temp_max_c']     = yr['temp_mean_c'] + yr['spread'] * 0.4
        yr['temp_min_c']     = yr['temp_mean_c'] - yr['spread'] * 0.4
        yr['HDD']            = (15.5 - yr['temp_mean_c']).clip(lower=0) * 30
        yr['CDD']            = (yr['temp_mean_c'] - 18.0).clip(lower=0) * 30
        yr['temp_squared']   = yr['temp_mean_c'] ** 2
        yr['temp_roll7']     = yr['temp_mean_c']
        yr['day_of_year']    = yr['month'] * 30
        yr['temp_x_weekend'] = yr['temp_mean_c'] * 0.28
        yr['is_weekend']     = 0
        yr['weekday']        = 2
        yr['wind_mean_m_s']  = yr['wind']
        yr['solar_rad_j_m2'] = yr['solar']
        yr['precip_mm']      = yr['precip']
        yr['year_trend']     = 2030 - 2015

        yr['load_MW'] = model.predict(yr[FEATURES])
        annual_load   = yr['load_MW'].mean()
        annual_temp   = yr['temp_mean_c'].mean()
        loss_rate     = 0.065 + 0.004 * max(annual_temp - 11.5, 0)
        req_gen       = annual_load / (1 - loss_rate)
        wasted        = req_gen - annual_load

        records.append({
            'scenario':        scenario,
            'year':            year,
            'load_mean_MW':    round(annual_load, 1),
            'loss_rate_pct':   round(loss_rate * 100, 3),
            'extra_loss_pct':  round((loss_rate - 0.065) * 100, 3),
            'required_gen_MW': round(req_gen, 1),
            'wasted_MW':       round(wasted, 1),
            'temp_mean_c':     round(annual_temp, 3),
        })

df_proj = pd.DataFrame(records)
df_proj.to_csv('data/processed/demand_projections.csv', index=False)

print('Key results at 2050:')
for scenario in df_proj['scenario'].unique():
    r = df_proj[(df_proj['scenario'] == scenario) & (df_proj['year'] == 2050)].iloc[0]
    load   = r['load_mean_MW']
    wasted = r['wasted_MW']
    print(f'  {scenario}: {load:.0f} MW demand, {wasted:.0f} MW wasted')

colors = {'SSP1-2.6': '#2196F3', 'SSP2-4.5': '#FF9800', 'SSP5-8.5': '#F44336'}
hist_e = pd.read_csv('data/processed/master_dataset.csv')
hist_e['date'] = pd.to_datetime(hist_e['date'])
hist_e['year'] = hist_e['date'].dt.year
hist_annual = hist_e.groupby('year')['load_mean_MW'].mean().reset_index()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Projected Hungarian Electricity Demand Under Climate Scenarios', fontsize=13)

for scenario, color in colors.items():
    s = df_proj[df_proj['scenario'] == scenario]
    axes[0].plot(s['year'], s['load_mean_MW'], color=color, linewidth=2, label=scenario)
    axes[1].plot(s['year'], s['wasted_MW'], color=color, linewidth=2, label=scenario)
    axes[1].fill_between(s['year'], s['wasted_MW'], alpha=0.15, color=color)

axes[0].plot(hist_annual['year'], hist_annual['load_mean_MW'],
             color='#333333', linewidth=1.5, label='ENTSO-E observed')
axes[0].axvline(2024, color='gray', linestyle='--', linewidth=1, alpha=0.7)
axes[0].set_xlabel('Year')
axes[0].set_ylabel('Annual mean load (MW)')
axes[0].set_title('Climate-driven demand (structural trend removed)')
axes[0].legend(fontsize=9)
axes[0].grid(True, alpha=0.3)

axes[1].axvline(2024, color='gray', linestyle='--', linewidth=1, alpha=0.7)
axes[1].set_xlabel('Year')
axes[1].set_ylabel('Wasted energy (MW equivalent)')
axes[1].set_title('Energy lost to temperature-driven\ntransmission losses')
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results/figures/demand_projections.png', dpi=150, bbox_inches='tight')
print('Saved: results/figures/demand_projections.png')
plt.show()