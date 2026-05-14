"""
plot_style.py
-------------
Shared matplotlib style for all paper figures.
Import this at the top of every visualization script.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl

# Colorblind-friendly scenario palette
SCENARIO_COLORS = {
    "SSP1-2.6": "#1A85FF",
    "SSP2-4.5": "#FFA500",
    "SSP5-8.5": "#D41159",
}

SEASON_COLORS = {
    "Winter": "#1A85FF",
    "Spring": "#4CAF50",
    "Summer": "#D41159",
    "Autumn": "#FF8C00",
}

OBSERVED_COLOR = "#222222"
GRID_COLOR     = "#E0E0E0"
HIGHLIGHT      = "#534AB7"

def apply_style():
    mpl.rcParams.update({
        "font.family":        "DejaVu Sans",
        "font.size":          11,
        "axes.titlesize":     13,
        "axes.labelsize":     11,
        "xtick.labelsize":    10,
        "ytick.labelsize":    10,
        "legend.fontsize":    10,
        "figure.dpi":         150,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.grid":          True,
        "grid.color":         GRID_COLOR,
        "grid.linewidth":     0.8,
        "axes.axisbelow":     True,
        "figure.facecolor":   "white",
        "axes.facecolor":     "white",
        "savefig.bbox":       "tight",
        "savefig.dpi":        300,
    })