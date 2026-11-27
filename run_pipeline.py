
import argparse
from html import parser
import sys
from pathlib import Path

from src.ingestion import clean_grid_dataset
from src.analyzer import GridGenerationMixAnalyzer
from src.visualizer import (
    plot_southern_stack,
    plot_corr_and_deficits,
    build_plotly_dashboard,
)


def main():
    """Parse CLI arguments and run ingestion, analysis, and plotting end-to-end.

    Returns:
        int: 0 when pipeline finishes without errors.
    """
    parser = argparse.ArgumentParser(description="Run Project 15 Grid Analyzer Pipeline")
    parser.add_argument("--input", default="data/raw/daily_power_generation_india_raw.csv", help="Path to raw input CSV")
    parser.add_argument("--output-dir", default="data/processed", help="Folder for processed CSV and log")
    parser.add_argument("--report-dir", default="reports", help="Folder for figures and HTML report")
   
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    rep_dir = Path(args.report_dir)
    fig_dir = rep_dir / "figures"

    clean_csv = out_dir / "clean_daily_power_generation.csv"
    audit_log = out_dir / "power_grid_audit.log"

    print("Step 1: Auditing raw CSV and exporting clean dataset...")
    counts = clean_grid_dataset(args.input, clean_csv, audit_log)
    print(f"Total={counts['total']}, Valid={counts['valid']}, Rejected={counts['rejected']}")

    print("Step 2: Running GridGenerationMixAnalyzer models...")
    analyzer = GridGenerationMixAnalyzer(clean_csv)
    report = analyzer.summary_report()
    print("Southern Shannon H :", report["southern_shannon"]["mean_h"])
    print("OLS R2 Score       :", report["ols_model"]["r2"])
    print("Southern Aug-May   :", report["southern_monsoon_swing"])

    print("Step 3: Saving static figures and interactive Plotly HTML...")
    df = analyzer.get_data()
    plot_southern_stack(df, fig_dir / "primary_envelope.png")
    plot_corr_and_deficits(
        df,
        fig_dir / "correlation_heatmap.png",
        fig_dir / "distribution_regimes.png",
    )
    build_plotly_dashboard(df, rep_dir / "interactive_dashboard.html")
    print("Done! All artifacts saved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
