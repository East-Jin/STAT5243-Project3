from __future__ import annotations

import pandas as pd
from shiny import reactive

from shared.sample_datasets import get_titanic


class SharedDataStore:
    """Central reactive data store shared across all modules.

    Pipeline stages:
        raw_data        <- set by Data Loading module
        cleaned_data    <- set by Data Cleaning module
        engineered_data <- set by Feature Engineering module

    Each value is a reactive.value holding a pandas DataFrame (or None).
    """

    def __init__(self):
        self.raw_data: reactive.value[pd.DataFrame | None] = reactive.value(None)
        self.cleaned_data: reactive.value[pd.DataFrame | None] = reactive.value(None)
        self.engineered_data: reactive.value[pd.DataFrame | None] = reactive.value(None)
        self.data_info: reactive.value[dict] = reactive.value({})

    def get_latest_data(self) -> pd.DataFrame | None:
        """Return the most-processed DataFrame available."""
        for stage in [self.engineered_data, self.cleaned_data, self.raw_data]:
            df = stage()
            if df is not None:
                return df
        return None

    def get_latest_stage_name(self) -> str:
        """Return the name of the most-processed stage available."""
        if self.engineered_data() is not None:
            return "engineered"
        if self.cleaned_data() is not None:
            return "cleaned"
        if self.raw_data() is not None:
            return "raw"
        return "none"

    def reset_downstream(self):
        """Clear cleaned and engineered data (called when a new raw dataset is loaded)."""
        self.cleaned_data.set(None)
        self.engineered_data.set(None)

    def has_downstream_data(self) -> bool:
        return self.cleaned_data() is not None or self.engineered_data() is not None

    def dev_mode_init(self):
        """Pre-fill all pipeline stages with Titanic data for independent testing."""
        df = get_titanic()
        self.raw_data.set(df)
        self.cleaned_data.set(df.copy())
        self.engineered_data.set(df.copy())
        self.data_info.set(
            {
                "filename": "Titanic (dev mode)",
                "format": "Built-in",
                "rows": df.shape[0],
                "columns": df.shape[1],
            }
        )
