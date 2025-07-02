from crewai.tools import BaseTool
from typing import Type, Optional, List, Dict, Any, Union
from crewai.tools import BaseTool
from typing import Type, Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import io # Import io for StringIO


class ComprehensiveDataAnalyzerInput(BaseModel):
    """Input schema for the ComprehensiveDataAnalyzer tool."""
    input_data: str = Field(
        description="CSV content string OR CSV file name to analyze. Must be provided with every tool call."
    )
    operation: Optional[str] = Field(
        default="summary",
        description="Any one and Only one Operation at a time can be performed from this list: summary, full_data, count, columns, stats, correlation, group_by, filter, aggregate, top_values, time_series"
    )
    filter_condition: Optional[str] = Field(
        default=None,
        description="Simple filter condition (e.g., 'column>value')"
    )
    columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to include in analysis"
    )
    n_records: Optional[int] = Field(
        default=10,
        description="Number of records to return"
    )
    group_by_columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to group by"
    )
    aggregate_functions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Aggregation functions to apply"
    )
    date_column: Optional[str] = Field(
        default=None,
        description="Date column for time series"
    )
    time_freq: Optional[str] = Field(
        default=None,
        description="Time frequency (D=daily, W=weekly, M=monthly)"
    )


class ComprehensiveDataAnalyzer(BaseTool):
    """
    Tool for comprehensive data analysis of CSV files, ensuring ALL records are analyzed.
    """
    name: str = "ComprehensiveDataAnalyzer"
    description: str = """
    Analyze the complete dataset from a CSV file (provided as content string or path) to ensure ALL records are included.
    This tool provides direct access to the entire dataset.
    """
    args_schema: Type[BaseModel] = ComprehensiveDataAnalyzerInput
    # csv_path: Optional[str] = None # Removed csv_path attribute

    def __init__(self): # Removed csv parameter from init
        """Initialize the tool."""
        super().__init__()
        # No default path stored in the tool itself anymore

    def _get_dataframe(self, input_data: str) -> pd.DataFrame:
        """
        Load data into a pandas DataFrame.
        Tries loading as a file path first if input looks like a path,
        otherwise assumes input is CSV content string.
        """
        is_likely_path = "/" in input_data or "\\" in input_data or input_data.lower().endswith(".csv")
        df = None
        error_messages = []

        # Attempt 1: Load as Path if it looks like one
        if is_likely_path:
            try:
                # Construct the path carefully - assume relative to project root or data folder
                potential_path = input_data
                if not os.path.exists(potential_path):
                    # If simple filename or relative path doesn't exist, check inside ./data/
                    potential_path = os.path.join(os.getcwd(), "data", os.path.basename(input_data)) # Use absolute path
                    if not os.path.exists(potential_path):
                        # If neither exists, raise FileNotFoundError before pd.read_csv
                        raise FileNotFoundError(f"CSV file not found at '{input_data}' or '{potential_path}'")

                print(f"Info: Attempting to load DataFrame from path: {potential_path}")
                df = pd.read_csv(potential_path)
                print(f"Info: Successfully loaded DataFrame from path '{potential_path}'. Shape: {df.shape}")
                return df # Success loading as path
            except FileNotFoundError as e:
                error_messages.append(f"FileNotFoundError: {e}")
                # Don't return yet, might still be content
            except Exception as e_path:
                error_messages.append(f"Error loading as path '{potential_path}': {e_path}")
                # Don't return yet, might still be content

        # Attempt 2: Load as Content String (if not loaded as path or path loading failed)
        if df is None:
            print("Info: Attempting to load DataFrame from input string as CSV content.")
            try:
                df = pd.read_csv(io.StringIO(input_data))
                # Check if loading as string resulted in the path being the header
                if len(df) == 0 and len(df.columns) == 1 and str(df.columns[0]) == input_data:
                    raise ValueError("Input string was parsed as header, not CSV content.")
                print(f"Info: Successfully loaded DataFrame from string content. Shape: {df.shape}")
                return df # Success loading as content
            except Exception as e_string:
                error_messages.append(f"Error loading as string content: {e_string}")

        # If both attempts failed
        raise ValueError(f"Failed to load CSV data. Input was: '{input_data[:100]}...'. Errors encountered: {'; '.join(error_messages)}")

    def _execute_filter(self, df: pd.DataFrame, filter_condition: str) -> pd.DataFrame:
        """Execute a simple filter condition on the DataFrame."""
        if not filter_condition:
            return df

        try:
            # Parse simple conditions like "column>value", "column==value", etc.
            operators = ['==', '!=', '>=', '<=', '>', '<', 'contains']

            op = None
            for operator in operators:
                if operator in filter_condition:
                    op = operator
                    break

            if not op:
                return df

            parts = filter_condition.split(op)
            if len(parts) != 2:
                return df

            column = parts[0].strip()
            value = parts[1].strip()

            # Try to convert value to numeric if possible
            try:
                value = float(value)
            except ValueError:
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

            # Apply the filter
            if op == '==':
                return df[df[column] == value]
            elif op == '!=':
                return df[df[column] != value]
            elif op == '>':
                return df[df[column] > value]
            elif op == '<':
                return df[df[column] < value]
            elif op == '>=':
                return df[df[column] >= value]
            elif op == '<=':
                return df[df[column] <= value]
            elif op == 'contains':
                return df[df[column].astype(str).str.contains(str(value), na=False)]

        except Exception as e:
            raise ValueError(f"Error applying filter: {str(e)}")

        return df

    def _format_output(self, result: Union[pd.DataFrame, pd.Series, Dict, str], max_rows: int = 10) -> str:
        """Format the output to be readable in string format."""
        if isinstance(result, pd.DataFrame):
            if len(result) > max_rows:
                return (
                    f"Total Records: {len(result)}\n\n"
                    f"First {max_rows//2} Records:\n{result.head(max_rows//2).to_string()}\n\n"
                    f"Last {max_rows//2} Records:\n{result.tail(max_rows//2).to_string()}\n\n"
                    f"Note: Showing {max_rows} out of {len(result)} total records.\n"
                    f"Column Names: {', '.join(result.columns.tolist())}\n"
                )
            else:
                return f"Total Records: {len(result)}\n\nAll Records:\n{result.to_string()}\n"

        elif isinstance(result, pd.Series):
            return f"{result.name}:\n{result.to_string()}\n"

        elif isinstance(result, dict):
            return json.dumps(result, indent=2, default=str)

        else:
            return str(result)

    def _run(self, input_data: str, operation: str = "summary", filter_condition: str = None,
             columns: List[str] = None, n_records: int = 10, group_by_columns: List[str] = None,
             aggregate_functions: Dict[str, Any] = None, date_column: str = None, time_freq: str = None) -> str:
        """Run comprehensive data analysis on the COMPLETE dataset."""
        try:
            # Load the DataFrame using the updated _get_dataframe method
            df = self._get_dataframe(input_data)
            total_records = len(df)

            # Apply filter if provided
            if filter_condition:
                df = self._execute_filter(df, filter_condition)
                filtered_records = len(df)
            else:
                filtered_records = total_records

            # Select columns if specified
            if columns:
                # Verify all columns exist
                valid_columns = [col for col in columns if col in df.columns]
                if not valid_columns:
                    return f"Error: None of the specified columns {columns} exist in the dataset. Available columns: {df.columns.tolist()}"
                df = df[valid_columns]

            # Perform the requested operation
            if operation == "summary":
                # Comprehensive data summary
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                date_cols = [col for col in df.columns if df[col].dtype == 'datetime64[ns]']

                # Try to convert string columns to datetime
                for col in df.columns:
                    if col in categorical_cols:
                        try:
                            df[col] = pd.to_datetime(df[col])
                            categorical_cols.remove(col)
                            date_cols.append(col)
                        except:
                            pass

                summary = {
                    "dataset_info": {
                        "total_records": total_records,
                        "filtered_records": filtered_records,
                        "columns": len(df.columns),
                        "numeric_columns": len(numeric_cols),
                        "categorical_columns": len(categorical_cols),
                        "date_columns": len(date_cols),
                        "memory_usage": f"{df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB"
                    },
                    "column_types": {
                        "numeric": numeric_cols,
                        "categorical": categorical_cols,
                        "date": date_cols
                    },
                    "statistics": {
                        "numeric": df[numeric_cols].describe().to_dict() if numeric_cols else {},
                        "categorical": {
                            col: df[col].value_counts().head(5).to_dict()
                            for col in categorical_cols[:min(5, len(categorical_cols))]
                        } if categorical_cols else {},
                        "missing_values": df.isnull().sum().to_dict(),
                        "sample_data": df.head(5).to_dict(orient='records')
                    }
                }
                return json.dumps(summary, indent=2, default=str)

            elif operation == "full_data":
                # Return the complete dataset (with reasonable formatting)
                return self._format_output(df, max_rows=n_records)

            elif operation == "count":
                # Simple record count with metadata
                result = {
                    "total_records": total_records,
                    "filtered_records": filtered_records,
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "memory_usage": f"{df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB"
                }
                return json.dumps(result, indent=2)

            elif operation == "columns":
                # Get detailed column information
                result = {
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "data_types": df.dtypes.astype(str).to_dict(),
                    "non_null_counts": df.count().to_dict(),
                    "missing_percentages": (df.isnull().mean() * 100).round(2).to_dict()
                }
                return json.dumps(result, indent=2)

            elif operation == "stats":
                # Comprehensive statistics
                result = f"Dataset Statistics (All {total_records} Records)\n\n"

                # Numeric statistics
                num_df = df.select_dtypes(include=[np.number])
                if not num_df.empty:
                    result += f"Numeric Columns Statistics:\n{num_df.describe().to_string()}\n\n"

                # Categorical value counts
                cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                if cat_cols:
                    result += "Categorical Columns - Top Values:\n"
                    for col in cat_cols[:min(5, len(cat_cols))]:
                        result += f"\n{col}:\n{df[col].value_counts().head(5).to_string()}\n"

                    if len(cat_cols) > 5:
                        result += f"\n(Showing 5 of {len(cat_cols)} categorical columns)\n"

                # Missing values
                missing = df.isnull().sum()
                missing = missing[missing > 0]
                if not missing.empty:
                    result += f"\nMissing Values:\n{missing.to_string()}\n"
                else:
                    result += "\nNo missing values found.\n"

                return result

            elif operation == "correlation":
                # Correlation analysis for numeric columns
                num_df = df.select_dtypes(include=[np.number])
                if num_df.empty:
                    return "No numeric columns found for correlation analysis."

                corr_matrix = num_df.corr()

                # Identify strong correlations
                strong_corr = {}
                for i, col1 in enumerate(corr_matrix.columns):
                    for col2 in corr_matrix.columns[i+1:]:
                        corr_value = corr_matrix.loc[col1, col2]
                        if abs(corr_value) > 0.7:  # Strong correlation threshold
                            strong_corr[f"{col1} - {col2}"] = corr_value

                result = f"Correlation Matrix (All {filtered_records} Records):\n\n"
                result += f"{corr_matrix.to_string()}\n\n"

                if strong_corr:
                    result += "Strong Correlations (|r| > 0.7):\n"
                    for pair, value in sorted(strong_corr.items(), key=lambda x: abs(x[1]), reverse=True):
                        result += f"{pair}: {value:.4f}\n"

                return result

            elif operation == "group_by":
                # Group by analysis
                if not group_by_columns:
                    return "Error: 'group_by_columns' must be specified for group_by operation."

                # Verify all group_by columns exist
                valid_group_columns = [col for col in group_by_columns if col in df.columns]
                if not valid_group_columns:
                    return f"Error: None of the group by columns {group_by_columns} exist in the dataset. Available columns: {df.columns.tolist()}"

                # Default aggregation if not specified
                if not aggregate_functions:
                    # Auto-detect numeric columns for aggregation
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.difference(pd.Index(valid_group_columns))
                    if not numeric_cols.empty:
                        aggregate_functions = {col: 'mean' for col in numeric_cols[:3]}  # Take first 3 numeric columns
                        aggregate_functions.update({numeric_cols[0]: 'count'})  # Add count for first column

                if not aggregate_functions:
                    # If no numeric columns for aggregation, just count records
                    grouped = df.groupby(valid_group_columns).size().reset_index(name='count')
                else:
                    # Apply specified aggregations
                    grouped = df.groupby(valid_group_columns).agg(aggregate_functions).reset_index()

                return self._format_output(grouped.sort_values(by=grouped.columns[-1], ascending=False), max_rows=n_records)

            elif operation == "filter":
                # Filter data is already applied above
                return self._format_output(df, max_rows=n_records)

            elif operation == "aggregate":
                # Aggregation analysis
                if not aggregate_functions:
                    # Auto-detect numeric columns for aggregation
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if not numeric_cols.empty:
                        aggregate_functions = {
                            col: ['count', 'mean', 'sum', 'min', 'max', 'std']
                            for col in numeric_cols[:3]  # Take first 3 numeric columns
                        }

                if not aggregate_functions:
                    return "Error: No numeric columns found for aggregation and no aggregate_functions specified."

                # Apply aggregations
                agg_result = df.agg(aggregate_functions)

                return self._format_output(agg_result)

            elif operation == "top_values":
                # Top/bottom values for each column
                result = f"Top Values Analysis (from {filtered_records} Records):\n\n"

                for col in df.columns[:min(10, len(df.columns))]:
                    result += f"\nColumn: {col}\n"
                    if df[col].dtype in [np.number, 'int64', 'float64']:
                        result += f"Top {min(5, len(df))} highest values:\n"
                        result += f"{df.nlargest(min(5, len(df)), col)[col].to_string()}\n\n"
                        result += f"Top {min(5, len(df))} lowest values:\n"
                        result += f"{df.nsmallest(min(5, len(df)), col)[col].to_string()}\n"
                    else:
                        result += f"Most frequent values:\n"
                        result += f"{df[col].value_counts().head(5).to_string()}\n"

                if len(df.columns) > 10:
                    result += f"\n(Showing analysis for 10 of {len(df.columns)} columns)\n"

                return result

            elif operation == "time_series":
                # Time series analysis
                if not date_column:
                    # Try to find date columns
                    date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
                    if date_cols:
                        date_column = date_cols[0]
                    else:
                        return "Error: 'date_column' must be specified for time_series operation."

                if date_column not in df.columns:
                    return f"Error: Date column '{date_column}' not found in dataset. Available columns: {df.columns.tolist()}"

                # Convert to datetime
                try:
                    df[date_column] = pd.to_datetime(df[date_column])
                except Exception as e:
                    return f"Error converting '{date_column}' to datetime: {str(e)}"

                # Set default time frequency if not specified
                if not time_freq:
                    time_freq = 'M'  # Monthly by default

                # Find numeric columns for analysis
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if not numeric_cols:
                    return "Error: No numeric columns found for time series analysis."

                # Select a few important numeric columns
                if len(numeric_cols) > 3:
                    numeric_cols = numeric_cols[:3]

                # Resample time series
                df = df.sort_values(by=date_column)
                df.set_index(date_column, inplace=True)

                try:
                    time_series = df[numeric_cols].resample(time_freq).agg(['count', 'sum', 'mean'])
                    return self._format_output(time_series, max_rows=n_records)
                except Exception as e:
                    return f"Error performing time series analysis: {str(e)}"

            else:
                return f"Error: Unknown operation '{operation}'. Use one of: summary, full_data, count, columns, stats, correlation, group_by, filter, aggregate, top_values, or time_series."

        except Exception as e:
            return f"Error processing data: {str(e)}"
