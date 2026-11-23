"""Charts for the README and the portfolio, built from data/marts (run after `dbt build`)."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MARTS, OUT = ROOT / "data" / "marts", ROOT / "docs" / "img"
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # validated categorical slots 1-4

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
})


def headline():
    y = pd.read_csv(MARTS / "agg_year.csv").sort_values("year")
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True, gridspec_kw={"hspace": 0.35})
    for ax, col, title, fmt in [
        (axes[0], "inscritos", "Inscritos no vestibular da UFSC (1ª opção)", "{:,.0f}"),
        (axes[1], "candidatos_por_vaga", "Candidatos por vaga", "{:.1f}"),
    ]:
        ax.plot(y.year, y[col], color=SERIES[0], linewidth=2)
        normal = y[~y.is_atypical_year]
        ax.scatter(normal.year, normal[col], s=22, color=SERIES[0], zorder=3, edgecolor=SURFACE, linewidth=1.5)
        odd = y[y.is_atypical_year]
        ax.scatter(odd.year, odd[col], s=40, facecolor=SURFACE, edgecolor=SERIES[0], linewidth=2, zorder=3)
        for yr in (2005, 2025):
            v = y.loc[y.year == yr, col].iloc[0]
            ax.annotate(fmt.format(v).replace(",", "X").replace(".", ",").replace("X", "."), (yr, v), textcoords="offset points",
                        xytext=(0, 9), ha="center", fontsize=10, color=INK, fontweight="bold")
        ax.set_title(title, loc="left", fontsize=12, color=INK, pad=10)
        ax.set_ylim(0, y[col].max() * 1.18)
        ax.axvspan(2019.5, 2025.5, color=GRID, alpha=0.35, linewidth=0)
    axes[0].yaxis.set_major_formatter(lambda v, _: f"{v/1000:.0f} mil")
    axes[0].text(2019.7, axes[0].get_ylim()[1] * 0.93, "vestibular unificado / pandemia", fontsize=9, color=MUTED)
    axes[1].text(2021, y.loc[y.year == 2021, "candidatos_por_vaga"].iloc[0] + 1.1, "2021: sem prova", fontsize=9, color=MUTED, ha="center")
    axes[1].set_xticks(range(2003, 2026, 2))
    fig.savefig(OUT / "ufsc_inscritos.png", dpi=150, bbox_inches="tight")


def areas():
    a = pd.read_csv(MARTS / "agg_area_year.csv")
    a = a[~a.is_atypical_year]
    groups = {
        "Saúde": a[a.subarea == "Saúde"],
        "Computação": a[a.subarea == "Computação"],
        "Engenharias": a[a.subarea == "Engenharia"],
        "Licenciaturas": a[a.degree_type == "Licenciatura"],
    }
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for (name, df), color in zip(groups.items(), SERIES):
        s = df.groupby("year").inscritos.sum()
        idx = 100 * s / s.loc[2005]
        ax.plot(idx.index, idx.values, color=color, linewidth=2, label=name)
        ax.annotate(f"{name}  {idx.iloc[-1]:.0f}", (idx.index[-1], idx.iloc[-1]), textcoords="offset points",
                    xytext=(6, 0), va="center", fontsize=10, color=INK)
    ax.axhline(100, color=MUTED, linewidth=1, linestyle=(0, (3, 3)))
    ax.set_title("Inscritos por área, índice 2005 = 100", loc="left", fontsize=12, color=INK, pad=10)
    ax.set_xticks(range(2005, 2026, 2)); ax.set_xlim(2004.5, 2028.5); ax.set_ylim(0, None)
    ax.legend(frameon=False, ncols=4, loc="upper left", bbox_to_anchor=(0, -0.08))
    fig.savefig(OUT / "ufsc_areas.png", dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    headline()
    areas()
