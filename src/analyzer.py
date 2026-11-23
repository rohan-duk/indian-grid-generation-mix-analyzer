# Contributor   : Rohan / @rohan-duk
# Reviewer      : T/ @teammate2_handle


from pathlib import Path
import numpy as np
import pandas as pd

VALID_REGIONS = {
    "Northern",
    "Western",
    "Southern",
    "Eastern",
    "North-Eastern",
}


class GridGenerationMixAnalyzer:
    """Encapsulated analyzer for daily regional power generation and deficits.

    Attributes:
        __data (pd.DataFrame): Private DataFrame storing cleaned grid records.
        __is_loaded (bool): Private flag indicating if CSV data has been loaded.
    """

    def __init__(self, csv_path=None):
        """Initialize the analyzer with empty private state.

        Args:
            csv_path (str or Path, optional): Path to clean CSV to load on start.
        """
        self.__data = None
        self.__is_loaded = False
        self._last_shannon = None

        if csv_path is not None and Path(csv_path).exists():
            self.load_from_csv(csv_path)

    def _require_loaded(self):
        """Check that data is loaded before running any calculations.

        Raises:
            RuntimeError: If load_from_csv() has not been called yet.
        """
        if not self.__is_loaded or self.__data is None:
            raise RuntimeError("Data not loaded yet. Call load_from_csv() first.")

    def load_from_csv(self, csv_path):
        """Load cleaned CSV into private DataFrame and add derived columns.

        Args:
            csv_path (str or Path): Path to clean_daily_power_generation.csv.

        Returns:
            int: Total number of rows loaded.

        Raises:
            FileNotFoundError: If csv_path does not exist.
            ValueError: If the CSV file is empty.
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Clean CSV not found: {path}")

        df = pd.read_csv(path)
        if df.empty:
            raise ValueError("The CSV file is empty.")

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(["Date", "Region"]).reset_index(drop=True)
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month

        df["clean_energy_ratio"] = (
            (df["Hydro_Gen_MU"] + df["Nuclear_Gen_MU"]) / df["Total_Gen_MU"]
        )
        df["monsoon_hydro_shift"] = np.where(
            df["Month"].isin([6, 7, 8, 9]), "Monsoon", "Non-Monsoon"
        )
        df["deficit_severity_tier"] = pd.cut(
            df["Deficit_MW"],
            bins=[-1.0, 100.0, 1000.0, 1e9],
            labels=["Low", "Moderate", "Critical"],
        )

        self.__data = df
        self.__is_loaded = True
        return len(self.__data)

    def get_data(self):
        """Return a safe copy of the loaded DataFrame.

        Returns:
            pd.DataFrame: Copy of internal dataframe.

        Raises:
            RuntimeError: If data is not loaded.
        """
        self._require_loaded()
        return self.__data.copy()

    def compute_shannon_diversity(self, region="Southern"):
        """Calculate vectorized Shannon Diversity Index H = -sum(p_i * ln(p_i)).

        Args:
            region (str): Official grid region name (default 'Southern').

        Returns:
            dict: Mean Shannon index, yearly breakdown, and np.allclose check.

        Raises:
            RuntimeError: If data is not loaded.
            ValueError: If region is not one of the 5 official grid regions.
        """
        self._require_loaded()
        if region not in VALID_REGIONS:
            raise ValueError(f"Unknown region '{region}'. Choose from {VALID_REGIONS}.")

        sub = self.__data[self.__data["Region"] == region].copy()

        # 2D NumPy array of generation values
        gen_matrix = sub[["Thermal_Gen_MU", "Nuclear_Gen_MU", "Hydro_Gen_MU"]].to_numpy(dtype=float)
        total_vec = sub["Total_Gen_MU"].to_numpy(dtype=float).reshape(-1, 1)
        shares = gen_matrix / total_vec

        # Avoid log(0) by replacing 0 shares with 1 before taking log (0 * log(1) = 0)
        safe_shares = np.where(shares > 1e-12, shares, 1.0)
        shannon_h = -np.sum(shares * np.log(safe_shares), axis=1)

        # Verify against column-by-column calculation using np.allclose
        p_t, p_n, p_h = shares[:, 0], shares[:, 1], shares[:, 2]
        term_t = np.where(p_t > 1e-12, p_t * np.log(np.where(p_t > 1e-12, p_t, 1.0)), 0.0)
        term_n = np.where(p_n > 1e-12, p_n * np.log(np.where(p_n > 1e-12, p_n, 1.0)), 0.0)
        term_h = np.where(p_h > 1e-12, p_h * np.log(np.where(p_h > 1e-12, p_h, 1.0)), 0.0)
        check_h = -(term_t + term_n + term_h)

        verified = bool(np.allclose(shannon_h, check_h))

        sub["shannon_diversity_index"] = shannon_h
        self.__data.loc[sub.index, "shannon_diversity_index"] = shannon_h
        by_year = sub.groupby("Year")["shannon_diversity_index"].mean().round(4).to_dict()

        out = {
            "region": region,
            "mean_h": round(float(np.mean(shannon_h)), 4),
            "yearly_h": by_year,
            "allclose_ok": verified,
            "nbytes": int(shannon_h.nbytes),
        }
        self._last_shannon = out
        return out

