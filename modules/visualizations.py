from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from config import PDF_COLORS, SCORE_LABELS

PRIMARY = PDF_COLORS["primary"]
ACCENT = PDF_COLORS["accent"]
MUTED = PDF_COLORS["muted"]
GRID = PDF_COLORS["grid"]
PANEL = PDF_COLORS["panel_alt"]
SUCCESS = PDF_COLORS["success"]
WARNING = PDF_COLORS["warning"]


def _figure_to_png(fig: plt.Figure) -> bytes:
    import io

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buffer.getvalue()


def build_scores_chart(scores: dict[str, int]) -> bytes | None:
    if not scores:
        return None
    labels = [SCORE_LABELS.get(metric, metric) for metric in scores]
    values = [scores[metric] for metric in scores]
    colors = [PRIMARY, ACCENT, SUCCESS, WARNING, MUTED]

    fig, ax = plt.subplots(figsize=(7.2, 3.6), facecolor=PANEL)
    ax.barh(labels, values, color=colors[: len(values)], alpha=0.92)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Score heuristique")
    ax.grid(axis="x", color=GRID, alpha=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="both", colors=PRIMARY)
    fig.tight_layout()
    return _figure_to_png(fig)


def build_theme_chart(dominant_themes: list[dict[str, Any]]) -> bytes | None:
    if not dominant_themes:
        return None
    labels = [item["theme"] for item in dominant_themes[:6]][::-1]
    values = [item["count"] for item in dominant_themes[:6]][::-1]

    fig, ax = plt.subplots(figsize=(7.2, 3.6), facecolor=PANEL)
    ax.barh(labels, values, color=ACCENT, alpha=0.9)
    ax.grid(axis="x", color=GRID, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="both", colors=PRIMARY)
    fig.tight_layout()
    return _figure_to_png(fig)


def build_profile_history_chart(profile: dict[str, Any]) -> bytes | None:
    score_trends = profile.get("score_trends", {})
    if not score_trends:
        return None

    tracked_metrics = ["clarity", "action_orientation", "internal_coherence"]
    available_metrics = [metric for metric in tracked_metrics if len(score_trends.get(metric, [])) >= 2]
    if not available_metrics:
        return None

    fig, ax = plt.subplots(figsize=(7.4, 3.8), facecolor=PANEL)
    palette = [PRIMARY, ACCENT, SUCCESS]

    for index, metric in enumerate(available_metrics):
        history = score_trends.get(metric, [])
        values = [point["value"] for point in history]
        labels = [point.get("title") or f"S{position + 1}" for position, point in enumerate(history)]
        ax.plot(range(len(values)), values, marker="o", linewidth=2.2, color=palette[index], label=SCORE_LABELS.get(metric, metric))
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=20, ha="right")

    ax.set_ylim(0, 100)
    ax.grid(axis="y", color=GRID, alpha=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="both", colors=PRIMARY)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    return _figure_to_png(fig)
