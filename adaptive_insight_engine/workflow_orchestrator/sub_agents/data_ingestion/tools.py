"""
Tools for the Data Ingestion Agent: validate, parse, and clean uploaded datasets.
"""
import io
import pandas as pd
from typing import Optional

import base64

def parse_uploaded_file(file_content: str, file_name: str) -> dict:
    """
    Parse the uploaded file (CSV, Excel, or TXT) into a dictionary (records format).
    Supports both base64-encoded and plain text uploads.
    Returns a dict with a 'data' key containing the records, or a 'valid': False error message.
    """
    import pandas as pd
    import base64, io
    try:
        # Try base64 decode first
        try:
            file_bytes = base64.b64decode(file_content)
            if file_name.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_bytes))
            elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                df = pd.read_excel(io.BytesIO(file_bytes))
            elif file_name.endswith('.txt'):
                df = pd.read_csv(io.BytesIO(file_bytes))
            else:
                raise ValueError("Unsupported file type.")
        except Exception:
            # Fallback: treat as plain text
            if file_name.endswith('.csv') or file_name.endswith('.txt'):
                df = pd.read_csv(io.StringIO(file_content))
            elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                df = pd.read_excel(io.StringIO(file_content))
            else:
                raise ValueError("Unsupported file type or invalid encoding.")
        import numpy as np
        df_clean = df.replace({np.nan: None, np.inf: None, -np.inf: None})
        return {"valid": True, "data": df_clean.to_dict(orient="records")}
    except Exception as e:
        return {"valid": False, "reason": f"Failed to parse file: {e}"}

def validate_dataframe(df_dict: dict) -> dict:
    """
    Validate the DataFrame: check for missing values, infer schema, and basic stats.
    Accepts a dictionary (e.g., from df.to_dict(orient="records")) and converts it to a DataFrame.
    Returns a dict with validation results.
    """
    import pandas as pd
    if not df_dict:
        return {"valid": False, "reason": "No data provided."}
    try:
        df = pd.DataFrame(df_dict)
    except Exception as e:
        return {"valid": False, "reason": f"Failed to convert data to DataFrame: {e}"}
    return {
        "valid": True,
        "columns": list(df.columns),
        "num_rows": len(df),
        "num_missing": int(df.isnull().sum().sum()),
        "dtypes": df.dtypes.apply(str).to_dict(),
        "head": df.head(5).to_dict(orient="records"),
    }
