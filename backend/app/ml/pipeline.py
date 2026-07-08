import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import io
import re

class DataIngestionPipeline:
    def __init__(self):
        pass

    @staticmethod
    def parse_currency(val: Any) -> float:
        """Helper to convert string currencies (e.g. '$1,200', '1.2M', '10,000 INR') to numeric floats."""
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip().upper()
        # Remove currency symbols and commas
        val_str = re.sub(r'[$,₹£€\s,]', '', val_str)
        # Parse multiplier abbreviations
        multiplier = 1.0
        if val_str.endswith('K'):
            multiplier = 1000.0
            val_str = val_str[:-1]
        elif val_str.endswith('M'):
            multiplier = 1000000.0
            val_str = val_str[:-1]
        elif val_str.endswith('B'):
            multiplier = 1000000000.0
            val_str = val_str[:-1]
            
        try:
            return float(val_str) * multiplier
        except ValueError:
            return 0.0

    def ingest_bytes(self, data_bytes: bytes, filename: str) -> pd.DataFrame:
        """Ingests file from raw bytes (supports CSV and Excel)."""
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(data_bytes))
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(data_bytes))
        else:
            raise ValueError("Unsupported file format. Please upload CSV or Excel.")
        return df

    def detect_schema(self, df: pd.DataFrame) -> Dict[str, str]:
        """Automatically detects column types (numerical, categorical, text, date)."""
        schema = {}
        for col in df.columns:
            # Check if date
            try:
                if df[col].dtype == 'object':
                    # Check first few non-null elements
                    sample = df[col].dropna().head(5)
                    if len(sample) > 0 and all(isinstance(x, str) and re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}', x) for x in sample):
                        schema[col] = "date"
                        continue
            except Exception:
                pass

            # Numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                schema[col] = "numerical"
            else:
                # Check cardinality for Categorical vs Text
                non_null = df[col].dropna()
                if len(non_null) == 0:
                    schema[col] = "categorical"
                else:
                    unique_pct = len(non_null.unique()) / len(non_null)
                    if unique_pct < 0.15 or len(non_null.unique()) < 20:
                        schema[col] = "categorical"
                    else:
                        # Try parsing as currency
                        sample_parsed = non_null.head(5).apply(self.parse_currency)
                        if (sample_parsed > 0).sum() >= 3:
                            schema[col] = "numerical"
                        else:
                            schema[col] = "text"
        return schema

class DataPreprocessor:
    def __init__(self, schema: Dict[str, str]):
        self.schema = schema
        self.imputation_values = {}
        self.scaler_params = {}

    def clean_and_validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans, handles duplicates, missing values, outliers, and converts columns."""
        df_clean = df.copy()
        
        # 1. Deduplicate
        df_clean = df_clean.drop_duplicates()

        # 2. Schema alignment and conversion
        for col, col_type in self.schema.items():
            if col not in df_clean.columns:
                continue

            if col_type == "numerical":
                # Convert string currencies/numbers to floats
                if df_clean[col].dtype == 'object':
                    df_clean[col] = df_clean[col].apply(DataIngestionPipeline.parse_currency)
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                
                # Impute missing with median
                median_val = df_clean[col].median()
                if pd.isna(median_val):
                    median_val = 0.0
                df_clean[col] = df_clean[col].fillna(median_val)
                self.imputation_values[col] = median_val
                
                # Outlier treatment (cap at 1.5 * IQR)
                q25 = df_clean[col].quantile(0.25)
                q75 = df_clean[col].quantile(0.75)
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                df_clean[col] = np.clip(df_clean[col], lower_bound, upper_bound)
                
            elif col_type == "categorical":
                df_clean[col] = df_clean[col].astype(str).fillna("UNKNOWN")
                self.imputation_values[col] = "UNKNOWN"
                
            elif col_type == "date":
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                # Fill missing dates with current time
                df_clean[col] = df_clean[col].fillna(pd.Timestamp.now())
                
            elif col_type == "text":
                df_clean[col] = df_clean[col].astype(str).fillna("")
                self.imputation_values[col] = ""

        return df_clean
