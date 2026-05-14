import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

proj = pd.read_csv('data/processed/cmip6_projections.csv')
annual = proj.groupby(['scenario','year']).agg(
    HDD_sum=('HDD_monthly','sum'),
    CDD_sum=('CDD_monthly','sum'),
    temp=('temp_mean_c','mean'),
).reset_index()

# Baseline 2025
base = annual[annual['year']==2025].set_index('scenario')

colors = {'SSP1-2.6':'#2196F3','SSP2-4.5':'#FF9800','SSP5-8.5':'#F44336'}

fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle('Demand Composition Shift Under Climate Scenarios', fontsize=13)

for scenario, color in colors.items():
    s = annual[annual['scenario']==scenario]
    b = base.loc[scenario]

    axes[0].plot(s['year'], s['HDD_sum'], color=color, linewidth=2, label=scenario)
    axes[1].plot(s['year'], s['CDD_sum'], color=color, linewidth=2, label=scenario)

    # Net energy impact: CDD gain - HDD reduction (normalised to MW proxy)
    hdd_delta = s['HDD_sum'].values - b['HDD_sum']
    cdd_delta = s['CDD_sum'].values - b['CDD_sum']
    net = cdd_delta * 8 + hdd_delta * 5   # cooling is ~8MW/CDD, heating ~5MW/CDD
    axes[2].plot(s['year'], net, color=color, linewidth=2, label=scenario)
    axes[2].fill_between(s['year'], net, alpha=0.15, color=color)

for ax, title, ylabel in zip(axes,
    ['Heating demand (HDD)', 'Cooling demand (CDD)', 'Net demand shift vs 2025'],
    ['Annual HDD', 'Annual CDD', 'MW equivalent']):
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

axes[2].axhline(0, color='gray', linestyle='--', linewidth=1)

plt.tight_layout()
plt.savefig('results/figures/demand_composition.png', dpi=150, bbox_inches='tight')
print('Saved')
plt.show()