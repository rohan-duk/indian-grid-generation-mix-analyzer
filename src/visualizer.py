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


def plot_corr_and_deficits(df, heatmap_path, regimes_path):
    """Create Seaborn correlation heatmap and regional deficit boxplots (Q11).

    Args:
        df (pd.DataFrame): Cleaned grid dataframe.
        heatmap_path (str or Path): Output path for correlation_heatmap.png.
        regimes_path (str or Path): Output path for distribution_regimes.png.

    Returns:
        tuple: (Path to heatmap PNG, Path to regimes PNG).

    Raises:
        ValueError: If dataframe is empty.
    """
    if df.empty:
        raise ValueError("DataFrame cannot be empty.")

    h_out = Path(heatmap_path)
    r_out = Path(regimes_path)
    h_out.parent.mkdir(parents=True, exist_ok=True)

    # 2-panel figure: Heatmap on left, Regional Deficit Boxplot on right
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    num_cols = ["Thermal_Gen_MU", "Nuclear_Gen_MU", "Hydro_Gen_MU", "Total_Gen_MU", "Peak_Demand_MW", "Deficit_MW"]
    sns.heatmap(df[num_cols].corr(), annot=True, fmt=".2f", cmap="coolwarm", ax=ax1)
    ax1.set_title("Correlation Heatmap", fontweight="bold")

    sns.boxplot(data=df, x="Region", y="Deficit_MW", hue="monsoon_hydro_shift", ax=ax2)
    ax2.set_title("Regional Deficit by Season", fontweight="bold")
    ax2.tick_params(axis="x", rotation=20)
    sns.despine(fig=fig)
    plt.tight_layout()
    fig.savefig(h_out, dpi=300)
    plt.close(fig)

    # Violin distribution plot for distribution_regimes.png
    fig2, ax = plt.subplots(figsize=(9, 5))
    sns.violinplot(data=df, x="Region", y="clean_energy_ratio", hue="monsoon_hydro_shift", split=True, ax=ax)
    ax.set_title("Clean Energy Ratio Across Regions & Seasons", fontweight="bold")
    sns.despine(fig=fig2)
    plt.tight_layout()
    fig2.savefig(r_out, dpi=300)
    plt.close(fig2)

    return h_out, r_out


def build_plotly_dashboard(df, html_path):
    """Export standalone interactive Plotly HTML dashboard with date slider (Q12).

    Args:
        df (pd.DataFrame): Cleaned grid dataframe.
        html_path (str or Path): Output path for interactive_dashboard.html.

    Returns:
        Path: Path to generated HTML file.

    Raises:
        ValueError: If dataframe is empty.
    """
    if df.empty:
        raise ValueError("DataFrame cannot be empty.")

    out_html = Path(html_path)
    out_html.parent.mkdir(parents=True, exist_ok=True)

    daily = (
        df.groupby(["Date", "Region"], as_index=False)[
            ["Hydro_Gen_MU", "Nuclear_Gen_MU", "Thermal_Gen_MU", "Peak_Demand_MW", "Deficit_MW"]
        ]
        .sum()
        .sort_values("Date")
    )

    long_df = pd.melt(
        daily,
        id_vars=["Date", "Region", "Peak_Demand_MW", "Deficit_MW"],
        value_vars=["Hydro_Gen_MU", "Nuclear_Gen_MU", "Thermal_Gen_MU"],
        var_name="Energy_Source",
        value_name="Generation_MU",
    )

    fig = px.area(
        long_df,
        x="Date",
        y="Generation_MU",
        color="Energy_Source",
        facet_col="Region",
        facet_col_wrap=2,
        hover_data=["Peak_Demand_MW", "Deficit_MW"],
        title="Indian Grid Daily Generation Mix Dashboard (2017-2020)",
    )
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(height=700)
    fig.write_html(str(out_html), include_plotlyjs="cdn")
    return out_html
