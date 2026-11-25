"""
visualisation.py  -  Component 6: Visualisation and report
Owner: Swarnava Banerjee (25BTRDC053)
Creates labelled matplotlib charts in a dark "dashboard" style
and saves them in the charts/ folder.
"""
import os

import matplotlib
matplotlib.use("Agg")          # save to file, works without a display
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm

from analysis import grade_distribution, student_summary, subject_averages, subject_pass_rate

CHART_DIR = "charts"
BG, PANEL, TEXT, MUTED, GRID = "#0F172A", "#1E293B", "#F1F5F9", "#94A3B8", "#334155"
NEON = ["#22D3EE", "#A78BFA", "#F472B6", "#FBBF24", "#34D399", "#FB7185", "#60A5FA"]


def apply_style():
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": PANEL, "savefig.facecolor": BG,
        "axes.edgecolor": GRID, "axes.labelcolor": TEXT, "axes.titlecolor": TEXT,
        "axes.titlesize": 14, "axes.titleweight": "bold", "axes.labelsize": 11,
        "xtick.color": MUTED, "ytick.color": MUTED, "text.color": TEXT,
        "axes.grid": True, "grid.color": GRID, "grid.linestyle": "--", "grid.alpha": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "font.size": 11,
        "legend.facecolor": PANEL, "legend.edgecolor": GRID,
    })


def bar_subject_averages(df):
    avg = subject_averages(df)
    colors = cm.plasma(np.linspace(0.25, 0.9, len(avg)))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.bar(avg.index, avg.values, color=colors, width=0.6, edgecolor="white", linewidth=0.6, zorder=3)
    for bar, val in zip(bars, avg.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 3.5, f"{val:.1f}",
                ha="center", fontsize=13, fontweight="bold", color=TEXT)
    ax.axhline(avg.mean(), color=NEON[0], linestyle="--", linewidth=2, label=f"Class mean {avg.mean():.1f}", zorder=4)
    ax.annotate("Weakest subject", xy=(0, avg.values[0]), xytext=(0.6, avg.values[0] + 22),
                color=NEON[5], fontweight="bold", arrowprops=dict(arrowstyle="->", color=NEON[5], lw=2))
    ax.set_title("Average Marks by Subject")
    ax.set_xlabel("Subject")
    ax.set_ylabel("Average marks (out of 100)")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left")
    return save(fig, "1_subject_averages_bar.png")


def pie_grade_distribution(df):
    """Donut chart of grades with the total in the centre."""
    dist = grade_distribution(df)
    dist = dist[dist > 0]
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    wedges, _, autotexts = ax.pie(
        dist.values, labels=[f"Grade {g}" for g in dist.index], autopct="%1.1f%%",
        colors=NEON[:len(dist)], startangle=90, pctdistance=0.8,
        wedgeprops=dict(width=0.38, edgecolor=BG, linewidth=3),
        textprops=dict(color=TEXT, fontsize=12, fontweight="bold"))
    for t in autotexts:
        t.set_color(BG)
        t.set_fontsize(11)
    ax.text(0, 0.08, f"{dist.sum()}", ha="center", fontsize=34, fontweight="bold", color=TEXT)
    ax.text(0, -0.15, "marks graded", ha="center", fontsize=13, color=MUTED)
    ax.set_title("Grade Distribution (all subjects)", pad=15)
    return save(fig, "2_grade_distribution_pie.png")


def scatter_marks(df, pass_mark=40):
    """Maths vs Python, each dot coloured by the student's SGPA, with a trend line."""
    wide = df.pivot_table(index="usn", columns="subject", values="mark").dropna(subset=["Maths", "Python"])
    sgpa = student_summary(df, pass_mark).set_index("usn")["sgpa"].reindex(wide.index)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sc = ax.scatter(wide["Maths"], wide["Python"], c=sgpa, cmap="plasma", s=70,
                    edgecolors="white", linewidths=0.5, alpha=0.9, zorder=3)
    slope, intercept = np.polyfit(wide["Maths"], wide["Python"], 1)
    xs = np.linspace(wide["Maths"].min(), wide["Maths"].max(), 50)
    ax.plot(xs, slope * xs + intercept, color=NEON[0], linewidth=2.5, label="Trend line", zorder=4)
    r = np.corrcoef(wide["Maths"], wide["Python"])[0, 1]
    ax.text(0.02, 0.95, f"Correlation r = {r:.2f}", transform=ax.transAxes,
            fontsize=12, fontweight="bold", color=NEON[3], va="top")
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("SGPA", color=TEXT)
    cbar.ax.yaxis.set_tick_params(color=MUTED)
    plt.setp(cbar.ax.get_yticklabels(), color=MUTED)
    ax.set_title("Maths vs Python Marks (colour = SGPA)")
    ax.set_xlabel("Maths marks")
    ax.set_ylabel("Python marks")
    ax.legend(loc="lower right")
    return save(fig, "3_maths_vs_python_scatter.png")


def dashboard(df, pass_mark=40):
    """2 x 2 subplots dashboard."""
    summary = student_summary(df, pass_mark)
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.5))
    fig.suptitle("GRADEBOOK  ·  CLASS PERFORMANCE DASHBOARD", fontsize=18, fontweight="bold", color=NEON[0])

    # 1. SGPA histogram with gradient-coloured bars
    ax = axes[0, 0]
    n, bins, patches = ax.hist(summary["sgpa"], bins=12, edgecolor=BG, zorder=3)
    for p, c in zip(patches, cm.plasma(np.linspace(0.2, 0.95, len(patches)))):
        p.set_facecolor(c)
    ax.axvline(summary["sgpa"].mean(), color=NEON[0], linestyle="--", linewidth=2,
               label=f"Mean SGPA {summary['sgpa'].mean():.2f}")
    ax.set_title("SGPA Distribution")
    ax.set_xlabel("SGPA")
    ax.set_ylabel("Number of students")
    ax.legend()

    # 2. Pass rate by subject, labelled bars
    ax = axes[0, 1]
    rate = subject_pass_rate(df, pass_mark).sort_values()
    bars = ax.barh(rate.index, rate.values, color=[NEON[4] if v >= 95 else NEON[3] for v in rate.values], zorder=3)
    for bar, v in zip(bars, rate.values):
        ax.text(v - 2, bar.get_y() + bar.get_height() / 2, f"{v:.1f}%", va="center", ha="right",
                color=BG, fontweight="bold")
    ax.set_title("Pass Rate by Subject")
    ax.set_xlabel("Pass rate (%)")
    ax.set_xlim(0, 100)

    # 3. Result status donut
    ax = axes[1, 0]
    counts = summary["result"].value_counts()
    ax.pie(counts.values, labels=[f"{k}\n{v} students" for k, v in counts.items()],
           colors=[NEON[4], NEON[5], NEON[1]][:len(counts)], startangle=90,
           wedgeprops=dict(width=0.4, edgecolor=BG, linewidth=3), textprops=dict(color=TEXT, fontsize=11))
    complete = counts.sum() - counts.get("INCOMPLETE", 0)
    ax.text(0, 0, f"{counts.get('PASS', 0) / complete * 100:.1f}%\npassed", ha="center", va="center",
            fontsize=18, fontweight="bold", color=TEXT)
    ax.set_title("Result Status")

    # 4. Violin plot of marks by subject
    ax = axes[1, 1]
    subjects = sorted(df["subject"].unique())
    data = [df[df["subject"] == s]["mark"].dropna() for s in subjects]
    parts = ax.violinplot(data, showmeans=True)
    for body, c in zip(parts["bodies"], NEON):
        body.set_facecolor(c)
        body.set_edgecolor("white")
        body.set_alpha(0.75)
    for key in ("cbars", "cmins", "cmaxes", "cmeans"):
        parts[key].set_color(TEXT)
    ax.axhline(pass_mark, color=NEON[5], linestyle=":", linewidth=2, label=f"Pass mark {pass_mark}")
    ax.set_xticks(range(1, len(subjects) + 1), subjects, rotation=15)
    ax.set_title("Spread of Marks by Subject")
    ax.set_ylabel("Marks")
    ax.legend(loc="lower right")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return save(fig, "4_dashboard_subplots.png")


def save(fig, filename):
    os.makedirs(CHART_DIR, exist_ok=True)
    path = os.path.join(CHART_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def generate_all(df, pass_mark=40):
    apply_style()
    paths = [bar_subject_averages(df), pie_grade_distribution(df),
             scatter_marks(df, pass_mark), dashboard(df, pass_mark)]
    print("\nCharts saved:")
    for p in paths:
        print("  ", p)
    return paths
