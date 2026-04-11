"""
=============================================================================
PHASE 3: BEST-WORST METHOD (BWM) CALCULATOR
=============================================================================
This module solves the Linear BWM optimization problem (Rezaei, 2016).
It takes the Best-to-Others (BO) and Others-to-Worst (OW) vectors and 
computes the optimal weights for each criterion, along with the 
Consistency Ratio (CR).
"""

import numpy as np
from scipy.optimize import linprog

class BWMCalculator:
    def __init__(self, criteria_names):
        """
        Initializes the BWM model with a list of criteria names.
        """
        self.criteria = criteria_names
        self.n = len(criteria_names)
        
        # Consistency Index (CI) table for Linear BWM (Rezaei, 2016)
        # Indexes correspond to the max value in BO or OW vectors (usually 1 to 9)
        self.ci_table = {
            1: 0.00, 2: 0.44, 3: 1.00, 4: 1.63, 5: 2.30, 
            6: 3.00, 7: 3.73, 8: 4.47, 9: 5.23
        }

    def calculate_weights(self, best_criterion, worst_criterion, bo_vector, ow_vector):
        """
        Solves the linear optimization problem to find the criteria weights.
        
        :param best_criterion: string name of the most important criterion
        :param worst_criterion: string name of the least important criterion
        :param bo_vector: dictionary mapping {criterion: preference_score (1-9)}
        :param ow_vector: dictionary mapping {criterion: preference_score (1-9)}
        :return: dictionary of optimal weights, consistency ratio
        """
        # 1. Identify indices
        try:
            best_idx = self.criteria.index(best_criterion)
            worst_idx = self.criteria.index(worst_criterion)
        except ValueError as e:
            raise ValueError(f"Criterion not found in the initialized list: {e}")

        # Ensure Best-to-Best and Worst-to-Worst are set to 1
        bo_vector[best_criterion] = 1
        ow_vector[worst_criterion] = 1

        # 2. Setup the Linear Programming Problem
        # Variables: w_1, w_2, ..., w_n, xi (we have n+1 variables)
        # Objective: Minimize xi (which is the last variable)
        c = np.zeros(self.n + 1)
        c[-1] = 1.0  
        
        A_ub = []
        b_ub = []
        
        # 3. Build Inequality Constraints (A_ub * x <= b_ub)
        for i, crit in enumerate(self.criteria):
            if i != best_idx:
                a_Bj = bo_vector[crit]
                
                # Constraint 1: w_B - a_Bj * w_j - xi <= 0
                row1 = np.zeros(self.n + 1)
                row1[best_idx] = 1
                row1[i] = -a_Bj
                row1[-1] = -1
                A_ub.append(row1)
                b_ub.append(0)
                
                # Constraint 2: -w_B + a_Bj * w_j - xi <= 0
                row2 = np.zeros(self.n + 1)
                row2[best_idx] = -1
                row2[i] = a_Bj
                row2[-1] = -1
                A_ub.append(row2)
                b_ub.append(0)

            if i != worst_idx:
                a_jW = ow_vector[crit]
                
                # Constraint 3: w_j - a_jW * w_W - xi <= 0
                row3 = np.zeros(self.n + 1)
                row3[i] = 1
                row3[worst_idx] = -a_jW
                row3[-1] = -1
                A_ub.append(row3)
                b_ub.append(0)
                
                # Constraint 4: -w_j + a_jW * w_W - xi <= 0
                row4 = np.zeros(self.n + 1)
                row4[i] = -1
                row4[worst_idx] = a_jW
                row4[-1] = -1
                A_ub.append(row4)
                b_ub.append(0)

        # 4. Build Equality Constraint (Sum of weights = 1)
        A_eq = np.zeros((1, self.n + 1))
        A_eq[0, :self.n] = 1
        b_eq = np.array([1])

        # 5. Variable Bounds (Weights >= 0, xi >= 0)
        bounds = [(0, None) for _ in range(self.n + 1)]

        # 6. Solve using SciPy's Simplex/Highs method
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

        if not res.success:
            raise Exception(
                f"Linear programming optimization failed: {res.message}. "
                "Please check your BO and OW vectors."
            )

        # 7. Extract Results
        optimal_weights = res.x[:self.n]
        xi_star = res.x[-1]
        
        # Zip into a clean dictionary
        weights_dict = {self.criteria[i]: round(optimal_weights[i], 4) for i in range(self.n)}

        # 8. Calculate Consistency Ratio (CR)
        # Find the maximum preference value used in the BO vector to get the correct CI
        max_preference = max(bo_vector.values())
        ci = self.ci_table.get(max_preference, self.ci_table.get(9)) # Default to max if out of bounds        
        
        consistency_ratio = xi_star / ci if ci != 0 else 0.0

        return weights_dict, round(consistency_ratio, 4)


# =============================================================================
# EXECUTION BLOCK (For Testing)
# =============================================================================
if __name__ == "__main__":
    # Example Scenario: Choosing a Car
    criteria = ["cost", "engine", "airbag", "fuel_economy", "aesthetics"]
    
    # 1. User selects Best and Worst
    best = "cost"
    worst = "aesthetics"
    
    # 2. User scores Best against all others (1 to 9)
    bo = {
        "engine": 3,
        "airbag": 2,
        "fuel_economy": 4,
        "aesthetics": 8
    }
    
    # 3. User scores all others against Worst (1 to 9)
    ow = {
        "cost": 8, # This must match bo["aesthetics"] for perfect logic, but BWM handles small deviations
        "engine": 5,
        "airbag": 6,
        "fuel_economy": 3
    }
    
    # 4. Run the Model
    bwm = BWMCalculator(criteria)
    weights, cr = bwm.calculate_weights(best, worst, bo, ow)
    
    print("\n🏆 BWM Optimization Results:")
    print("-" * 30)
    for c, w in sorted(weights.items(), key=lambda item: item[1], reverse=True):
        print(f"{c.ljust(15)}: {w:.2%}")
        
    print("-" * 30)
    print(f"📊 Consistency Ratio (CR): {cr}")
    if cr < 0.1:
        print("✅ Excellent! The decision vectors are highly consistent.")
    elif cr < 0.2:
        print("⚠️ Acceptable. There is some inconsistency, but results are valid.")
    else:
        print("❌ Inconsistent! The user should review their 1-9 ratings.")
    print("\n")