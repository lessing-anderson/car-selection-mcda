"""
=============================================================================
PHASE 2: DATA TRANSFORMATION & FEATURE ENGINEERING
=============================================================================
This module is 100% dynamic. It reads all business rules, input paths, 
delimiters, and logical gates exclusively from '001-features-config.yaml'.
"""

import pandas as pd
import yaml
import operator
from pathlib import Path

class DataTransformer:
    def __init__(self, config_name='step1_features_config.yaml', max_budget=120000):
        self.max_budget = max_budget

        script_dir = Path(__file__).resolve()
        config_path = script_dir.parent / config_name
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            print("✅ YAML Config loaded successfully.")
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: The file {config_path} was not found.")

    def _apply_hard_constraints(self, df):
        """Dynamically filters the DataFrame based strictly on YAML constraints."""
        print("Filter 1: Applying Hard Constraints dynamically...")
        original_size = len(df)
        
        ops = {
            '==': operator.eq, '!=': operator.ne,
            '>':  operator.gt, '<':  operator.lt,
            '>=': operator.ge, '<=': operator.le
        }
        
        for constraint in self.config.get('hard_constraints', []):
            feature = constraint.get('feature')
            cond = constraint.get('condition')
            val = constraint.get('value')
            
            # Dynamic Variable Injection
            if val == "USER_DEFINED_MAX_BUDGET":
                val = self.max_budget
                
            if feature in df.columns and cond in ops:
                operation = ops[cond]
                if isinstance(val, (int, float)):
                    df = df[operation(pd.to_numeric(df[feature], errors='coerce'), val)]
                else:
                    df = df[operation(df[feature], val)]
                print(f"  -> Applied constraint: {feature} {cond} {val}")
                
        print(f" -> Cars removed: {original_size - len(df)} | Remaining: {len(df)}")
        return df.copy()

    def _drop_columns(self, df):
        """Removes columns dynamically based on business rules AND mathematical variance."""
        print("Filter 2: Removing uninformative columns...")
        
        # 1. Business Exclusions
        business_drops = self.config.get('dropped_columns', {}).get('business_exclusions', [])
        if business_drops:
            df = df.drop(columns=business_drops, errors='ignore')
            print(f"  -> Dropped by Business Rule: {business_drops}")

        # 2. Automatic Zero-Variance Drops
        cols_before = set(df.columns)
        
        df = df.loc[:, df.nunique(dropna=False) > 1]
        
        cols_after = set(df.columns)
        auto_dropped = list(cols_before - cols_after)
        
        if auto_dropped:
            print(f"  -> Auto-dropped (Zero Variance): {auto_dropped}")
            
        return df

    def _apply_conditional_logic(self, df):
        """
        Executes various data cleaning and logical actions based on YAML.
        Acts as an Action Dispatcher (OR_GATE, FILL_NULL, REPLACE_EXACT).
        """
        print("Transformation 1: Applying Conditional Logic dynamically...")
        
        for cond in self.config.get('conditional_logic', []):
            feature = cond.get('feature')
            action = cond.get('action')
            
            # Skip if the target column doesn't exist in the database
            if feature not in df.columns:
                continue

            # ACTION: Logical OR across multiple columns
            if action == "OR_GATE":
                deps = cond.get('dependencies', [])
                valid_deps = [col for col in deps if col in df.columns]
                if valid_deps:
                    temp_df = df[valid_deps].fillna(False).astype(bool)
                    df[feature] = temp_df.any(axis=1).astype(float)
                    print(f"  -> Applied OR_GATE substitution for: {feature}")
                    
            # ACTION: Fill purely missing mathematical data (NaN)
            elif action == "FILL_NULL":
                fill_val = cond.get('value', 0.0)
                df[feature] = df[feature].fillna(fill_val)
                print(f"  -> Applied FILL_NULL ({fill_val}) for: {feature}")
                
            # ACTION: Replace specific dirty text/strings
            elif action == "REPLACE_EXACT":
                target_val = cond.get('target') # e.g., 'n/a'
                new_val = cond.get('value')     # e.g., 1.0
                # Replaces the specific string and ensures pandas understands the change
                df[feature] = df[feature].replace(target_val, new_val)
                print(f"  -> Applied REPLACE_EXACT ('{target_val}' -> {new_val}) for: {feature}")
                
        return df

    def _apply_utility_mapping(self, df):
        print("Transformation 2: Applying Utility Mapping...")
        util_map = self.config.get('utility_mapping', {})
        for feature, mappings in util_map.items():
            if feature in df.columns:
                score_dict = {k: v['score'] for k, v in mappings.items()}
                df[feature] = df[feature].map(score_dict).fillna(0.0)
        return df

    def _apply_binarization(self, df):
        print("Transformation 3: Binarizing booleans...")
        for col in self.config.get('direct_binarization', []):
            if col in df.columns:
                df[col] = df[col].astype(float)
        return df

    def _apply_normalization(self, df):
        print("Transformation 4: Continuous Normalization (Min-Max)...")
        norm_config = self.config.get('continuous_normalization', {})
        
        for col in norm_config.get('minimization_costs', []):
            if col in df.columns:
                max_val = df[col].max()
                min_val = df[col].min()
                df[col] = (max_val - df[col]) / (max_val - min_val) if max_val != min_val else 1.0

        for col in norm_config.get('maximization_benefits', []):
            if col in df.columns:
                max_val = df[col].max()
                min_val = df[col].min()
                df[col] = (df[col] - min_val) / (max_val - min_val) if max_val != min_val else 1.0
                    
        return df

    def execute_pipeline(self):
        """Executes the pipeline reading file paths and config entirely from YAML."""
        
        # 1. Read metadata from YAML
        pipe_info = self.config.get('pipeline_info', {})
        csv_path = pipe_info.get('source_file', 'data/car_database.csv')
        delimiter = pipe_info.get('delimiter', ';')
        id_cols = pipe_info.get('id_columns', ['car', 'version'])
        
        print(f"\n🚀 Starting ETL pipeline for file: {csv_path}")
        
        # 2. Load Data
        script_dir = Path(__file__).resolve()
        csv_path = script_dir.parent.parent / csv_path

        print(csv_path)

        df_raw = pd.read_csv(csv_path, delimiter=delimiter)
        
        # 3. Preserve identifiers safely (dynamically)
        existing_id_cols = [col for col in id_cols if col in df_raw.columns]
        identifiers = df_raw[existing_id_cols].copy()
        
        # 4. Pipeline Execution
        df = self._apply_hard_constraints(df_raw)
        df = self._drop_columns(df)
        df = self._apply_conditional_logic(df)
        df = self._apply_utility_mapping(df)
        df = self._apply_binarization(df)
        df = self._apply_normalization(df)
        
        # 5. Restore identifiers
        for col in existing_id_cols:
            df[col] = identifiers[col]
        
        print("✅ Pipeline Finished! Mathematical matrix generated successfully.\n")
        return df

# =============================================================================
# EXECUTION BLOCK
# =============================================================================
if __name__ == "__main__":
    transformer = DataTransformer(config_name='step1_features_config.yaml', max_budget=105000)
    df_normalized = transformer.execute_pipeline()
    
    pd.set_option('display.max_columns', None)
    print("SAMPLE OF NORMALIZED DATA (Top 3 rows):")
    print(df_normalized.head(3))