from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px


def plot_southern_stack(df, save_path):
    """Plot Southern Region stacked daily generation and peak demand curve (Q10).

    Args:
        df (pd.DataFrame): Cleaned grid dataframe.
        save_path (str or Path): File path to save primary_envelope.png.

    Returns:
        Path: Path to saved PNG image.

    Raises:
        ValueError: If no Southern region rows exist in df.
    """
    south = df[df["Region"] == "Southern"].copy()
    if south.empty:
        raise ValueError("No Southern region records found for plotting.")

    daily = (
        south.groupby("Date", as_index=False)[
            ["Hydro_Gen_MU", "Nuclear_Gen_MU", "Thermal_Gen_MU", "Total_Gen_MU", "Peak_Demand_MW"]
        ]
        .sum()
        .sort_values("Date")
    )

    out_path = Path(save_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax1 = plt.subplots(figsize=(12, 5.5))
    ax1.stackplot(
        daily["Date"],
        daily["Hydro_Gen_MU"],
        daily["Nuclear_Gen_MU"],
        daily["Thermal_Gen_MU"],
        labels=["Hydro (MU)", "Nuclear (MU)", "Thermal (MU)"],
        colors=["#2b8cbe", "#7bccc4", "#e34a33"],
        alpha=0.8,
    )

    low_band = daily["Total_Gen_MU"].rolling(30, min_periods=3).quantile(0.25)
    high_band = daily["Total_Gen_MU"].rolling(30, min_periods=3).quantile(0.75)
    ax1.fill_between(daily["Date"], low_band, high_band, color="black", alpha=0.15, label="30-Day IQR Band")

    ax1.set_xlabel("Date")
    ax1.set_ylabel("Daily Generation (MU)")

    ax2 = ax1.twinx()
    ax2.plot(daily["Date"], daily["Peak_Demand_MW"], color="black", linestyle="--", linewidth=1.1, label="Peak Demand (MW)")
    ax2.set_ylabel("Peak Demand (MW)")
    ax2.grid(False)

    max_row = daily.loc[daily["Total_Gen_MU"].idxmax()]
    ax1.annotate(
        f"Max: {max_row['Total_Gen_MU']:.0f} MU",
        xy=(max_row["Date"], max_row["Total_Gen_MU"]),
        xytext=(max_row["Date"], max_row["Total_Gen_MU"] * 1.07),
        arrowprops={"arrowstyle": "->", "color": "black"},
    )

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left")

    plt.title("Southern Region Daily Generation Mix & Peak Demand (2017-2020)", fontweight="bold")
    plt.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path
