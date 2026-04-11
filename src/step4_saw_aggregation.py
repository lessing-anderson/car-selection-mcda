"""
=============================================================================
PHASE 4: SIMPLE ADDITIVE WEIGHTING (SAW) AGGREGATION
=============================================================================
This module takes the normalized mathematical matrix (Phase 2) and the 
user's criteria weights (Phase 3), multiplying them to generate the 
final recommendation ranking.
"""

import pandas as pd

class SAWCalculator:
    def __init__(self):
        """Initializes the SAW Calculator."""
        pass

    def calculate_ranking(self, df_normalized, weights_dict):
        """
        Calculates the final score for each alternative using the SAW method.
        
        :param df_normalized: Pandas DataFrame with normalized values (0.0 to 1.0)
        :param weights_dict: Dictionary mapping {criterion: weight}
        :return: DataFrame sorted by the Final Score in descending order
        """
        print("Aggregation: Calculating Final SAW Scores...")
        
        # Create a copy to avoid altering the original matrix
        df_result = df_normalized.copy()
        
        # Ensure we only calculate using columns that exist in BOTH the matrix and the weights
        valid_criteria = [col for col in weights_dict.keys() if col in df_result.columns]
        
        if not valid_criteria:
            raise ValueError("Error: None of the criteria in the weights dictionary match the DataFrame columns.")

        # Initialize the Final Score column with zeros
        df_result['Final_Score'] = 0.0
        
        # Vectorized multiplication: For each criterion, multiply the column by its weight and add to the total
        for criterion in valid_criteria:
            weight = weights_dict[criterion]
            df_result['Final_Score'] += df_result[criterion] * weight
            
        # Sort the DataFrame so the best cars are at the top
        df_result = df_result.sort_values(by='Final_Score', ascending=False).reset_index(drop=True)
        
        print("✅ Ranking generated successfully!")
        return df_result


# =============================================================================
# EXECUTION BLOCK (For Testing)
# =============================================================================
if __name__ == "__main__":
    # Mock data to test the script independently
    mock_data = {
        'car': ['Car A', 'Car B', 'Car C'],
        'version': ['Base', 'Top', 'Mid'],
        'cost': [0.8, 0.2, 0.5],       # Normalized values
        'engine': [0.4, 0.9, 0.6],
        'aesthetics': [0.5, 0.8, 0.7]
    }
    df_mock = pd.DataFrame(mock_data)
    
    mock_weights = {
        'cost': 0.60,
        'engine': 0.30,
        'aesthetics': 0.10
    }
    
    saw = SAWCalculator()
    df_ranked = saw.calculate_ranking(df_mock, mock_weights)
    
    print("\n🏆 Top 3 Recommended Cars:")
    print(df_ranked[['car', 'version', 'Final_Score']])