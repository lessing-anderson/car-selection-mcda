"""
=============================================================================
PHASE 4: HIERARCHICAL WEIGHT AGGREGATOR
=============================================================================
This module bridges the gap between human cognition and the SAW mathematical 
model. It takes the Macro category weights and distributes them among the 
Micro features (either equally by default, or via custom BWM micro-weights).
"""

import yaml
from pathlib import Path

class HierarchicalAggregator:
    def __init__(self, config_name='step1_features_config.yaml'):
        """Loads the criteria groups from the YAML configuration."""

        script_dir = Path(__file__).resolve()
        config_path = script_dir.parent / config_name
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
                
            self.groups = self.config.get('criteria_groups', {})
            if not self.groups:
                raise ValueError("Error: 'criteria_groups' missing in step1_features_config.yaml.")
                
            print(f"✅ Hierarchical Groups loaded: {list(self.groups.keys())}")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: The file {config_path} was not found.")

    def generate_flat_weights(self, macro_weights, custom_micro_weights=None):
        """
        Multiplies Macro weights by Micro weights to generate absolute feature weights.
        
        :param macro_weights: dict {'cost': 0.40, 'safety': 0.30, ...}
        :param custom_micro_weights: dict of dicts {'safety': {'airbag': 0.8, 'rear_view_camera': 0.2}}
        :return: flat dictionary with absolute weights for all mapped CSV columns
        """
        if custom_micro_weights is None:
            custom_micro_weights = {}

        absolute_weights = {}

        for category, macro_weight in macro_weights.items():
            # Get the exact CSV columns that belong to this category from YAML
            features = self.groups.get(category, [])
            
            if not features:
                print(f"⚠️ Warning: Category '{category}' has no features mapped in YAML.")
                continue

            # SCENARIO A: The user customized the weights inside this specific category
            if category in custom_micro_weights:
                micro_w_dict = custom_micro_weights[category]
                
                for feat in features:
                    # Multiply Macro x Micro
                    local_weight = micro_w_dict.get(feat, 0.0)
                    absolute_weights[feat] = round(macro_weight * local_weight, 4)
                    
            # SCENARIO B: Default behavior (Equal Distribution)
            else:
                equal_weight = 1.0 / len(features)
                for feat in features:
                    absolute_weights[feat] = round(macro_weight * equal_weight, 4)

        # Validate if the math holds up (Sum should be very close to 1.0)
        total_sum = sum(absolute_weights.values())
        print(f"📊 Absolute Weights generated for {len(absolute_weights)} features (Sum: {total_sum:.4f})")
        
        return absolute_weights


# =============================================================================
# EXECUTION BLOCK (For Testing)
# =============================================================================
if __name__ == "__main__":
    # Mocking the YAML internally just for this standalone test to work instantly
    import yaml
    import os
    
    mock_yaml = """
    criteria_groups:
      cost: ["cost", "warranty"]
      safety: ["airbag", "rear_view_camera", "rear_parking_sensors"]
    """
    with open("temp_mock.yaml", "w") as f: f.write(mock_yaml)
    
    # 1. Initialize Aggregator
    aggregator = HierarchicalAggregator(config_name="step1_features_config.yaml")
    
    # 2. Imagine the BWM calculated these Macro Weights (Sum = 1.0)
    macro_bwm = {
        'cost': 0.60,
        'safety': 0.40
    }
    
    # 3. Imagine the user ONLY customized 'safety', leaving 'cost' as default equal split
    custom_micro = {
        'safety': {
            'airbag': 0.80,              # User deeply cares about Airbag
            'rear_view_camera': 0.15,
            'rear_parking_sensors': 0.05
        }
    }
    
    # 4. Generate Final Weights for SAW
    final_weights = aggregator.generate_flat_weights(macro_bwm, custom_micro)
    
    print("\n🏆 FINAL ABSOLUTE WEIGHTS (Macro * Micro):")
    for feature, weight in sorted(final_weights.items(), key=lambda item: item[1], reverse=True):
        print(f"  {feature.ljust(22)}: {weight:.2%}")
        
    os.remove("temp_mock.yaml") # Clean up