"""
Tools for the Core Analysis Agent: statistical and exploratory data analysis.
"""
import pandas as pd
from typing import Optional, Dict, Any

def describe_dataframe(data: dict) -> Dict[str, Any]:
    """
    Return descriptive statistics and info for the dataframe.
    Accepts a dictionary (e.g., from df.to_dict(orient="records")) and converts it to a DataFrame.
    """
    import pandas as pd
    if not data:
        return {"valid": False, "reason": "No data provided."}
    try:
        df = pd.DataFrame(data)
    except Exception as e:
        return {"valid": False, "reason": f"Failed to convert data to DataFrame: {e}"}
    import numpy as np
    # Replace all NaN and inf values with None for JSON compatibility
    df_clean = df.replace({np.nan: None, np.inf: None, -np.inf: None})
    describe_dict = df_clean.describe(include='all').replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict()
    corr_dict = df_clean.corr(numeric_only=True).replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict()
    return {
        "valid": True,
        "describe": describe_dict,
        "correlations": corr_dict,
        "missing": int(df.isnull().sum().sum()),
        "columns": list(df.columns),
        "dtypes": df.dtypes.apply(str).to_dict(),
    }

def find_anomalies(df_dict: dict, z_thresh: float = 3.0) -> Dict[str, Any]:
    """
    Find rows with outliers using z-score thresholding for numeric columns.
    Accepts a dictionary (e.g., from df.to_dict(orient="records")) and converts it to a DataFrame.
    """
    import pandas as pd
    if not df_dict:
        return {"valid": False, "reason": "No data provided."}
    try:
        df = pd.DataFrame(df_dict)
    except Exception as e:
        return {"valid": False, "reason": f"Failed to convert data to DataFrame: {e}"}
    if df is None or df.select_dtypes(include='number').empty:
        return {"valid": False, "reason": "No numeric data."}
    from scipy.stats import zscore
    numeric_df = df.select_dtypes(include='number')
    z_scores = numeric_df.apply(zscore)
    mask = (z_scores.abs() > z_thresh).any(axis=1)
    anomalies = df[mask]
    return {
        "valid": True,
        "num_anomalies": anomalies.shape[0],
        "anomalies": anomalies.head(10).to_dict(orient="records")
    }
