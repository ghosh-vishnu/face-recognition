from typing import Optional, Tuple
import logging

import matplotlib
matplotlib.use("Agg")  # IMPORTANT: backend-safe (no GUI)

import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------

DEFAULT_FIGSIZE = (10, 6)
DEFAULT_STYLE = "darkgrid"


# -------------------------------------------------------------------
# STYLE CONFIG (NO GLOBAL SIDE EFFECTS)
# -------------------------------------------------------------------

def configure_style(style: str = DEFAULT_STYLE) -> None:
    try:
        sns.set_theme(style=style)
    except Exception:
        logger.exception("Failed to configure seaborn style")


# -------------------------------------------------------------------
# FIGURE BUILDER
# -------------------------------------------------------------------

def build_plot(
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Tuple[int, int] = DEFAULT_FIGSIZE,
    style: str = DEFAULT_STYLE,
):

    configure_style(style)

    fig, ax = plt.subplots(figsize=figsize)

    if title:
        ax.set_title(str(title))
    if xlabel:
        ax.set_xlabel(str(xlabel))
    if ylabel:
        ax.set_ylabel(str(ylabel))

    return fig, ax


# -------------------------------------------------------------------
# FINALIZE & CLEANUP
# -------------------------------------------------------------------

def finalize_plot(fig) -> None:
    try:
        fig.tight_layout()
    except Exception:
        logger.exception("Failed during plot layout")

    finally:
        plt.close(fig) 
