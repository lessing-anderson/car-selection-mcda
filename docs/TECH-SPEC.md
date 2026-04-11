# Technical Specification: MCDA-Based Decision Support System

**Summary:** This document details the architecture of the recommendation engine for vehicle selection, configured as a Decision Support System using a hybrid MCDA (Multi-Criteria Decision Analysis) model. The model combines the BWM (Best-Worst Method) for weight extraction and SAW (Simple Additive Weighting) for the final score aggregation.

---

## Hybrid Pipeline Architecture (BWM + SAW)

### Phase 1: Problem Structuring & Hard Constraints
The initial phase responsible for defining the scope of the problem, loading the universe of options, and eliminating operational noise.

* **Definition of the Alternative Space ($A$):** Loading the dataset of zero-kilometer cars.
* **Definition of the Criteria Space ($C$):** Selection of the features (columns) to be evaluated by the model. Variables with zero variance (e.g., standard items that 100% of the dataset possesses, such as ABS Brakes) are automatically discarded from mathematical processing to optimize calculation.
* **Application of Hard Constraints:** Application of non-negotiable boolean rules to summarily eliminate unfeasible alternatives prior to scoring.
    * *Example:* `Transmission == Automatic` AND `Cost <= R$ 120,000`.
    * *Justification:* Prevents the compensatory effect of the model from approving vehicles that are over budget or incompatible with the baseline requirements.

### Phase 2: Feature Engineering & Hybrid Normalization (Data Transformation & Scaling)
This phase transforms variables of different magnitudes (Monetary Values, Horsepower, Booleans) into a standardized scale from $0.0$ to $1.0$, ensuring mathematical proportionality and fairness in the evaluation.

* **Direct Binarization (*Boolean Mapping*):** Applied to categorical variables where the mere presence of the item represents the total benefit.
    * *Rule:* `True` = $1.0$ / `False` = $0.0$.
* **Utility Functions and Discretization (*Utility Mapping*):** Manual non-linear mapping for variables whose perceived value is not directly proportional to their raw numerical scale.
    * *Objective:* To enforce realistic utility steps. *Example - Airbags:* $2$ = $0.5$ (Primary safety benefit achieved); $4$ = $0.8$; $6$ = $1.0$.
* **Conditional Imputation of Missing Data (*Conditional Imputation*):** Handling `NaN` values using heuristics based on complementary features of the same record.
    * *Example:* If *Fog Lights* = `NaN` AND *Full LED Headlights* = `True` $\rightarrow$ Assigned Score = $1.0$ (Functionality already provided by superior technology).
* **Linear Normalization (*Min-Max Scaler*):** Applied to continuous variables.
    * *Maximization (Benefits):* Focused on the highest value.
    * *Minimization (Costs):* Inverted formula, where the lowest raw value (e.g., the lowest price) receives the score closest to $1.0$.

### Phase 3.A: Macro-Level Preference Elicitation (Best-Worst Method)
Module dedicated to the algorithmic extraction of the decision-maker's preference function. To prevent cognitive overload and Consistency Ratio (CR) explosion in high-dimensional matrices (25+ variables), the traditional linear BWM is elevated to a hierarchical architecture.

* **Categorical Grouping:** The criteria space ($C$) is logically clustered into 5 to 7 Macro Categories (e.g., *Cost, Safety, Performance, Comfort*).
* **Best-Worst Identification:** The user defines the Absolutely Best/Most Important (*Best*) and the Absolutely Worst/Least Important (*Worst*) **exclusively** at the Macro Category level.
* **Preference Vectorization (Scale of 1 to 9):**
    * *Best-to-Others Vector:* Degree of superiority of the *Best* category over all others.
    * *Others-to-Worst Vector:* Degree of superiority of each category over the *Worst* category.
* **Minimax Optimization (*Weight Extraction*):** Mathematical processing of the vectors through a solver (SciPy linear programming) to minimize the inconsistency error. Generates a calibrated vector of **Macro Weights** ($W_{Macro}$), ensuring their sum equals $1.0$.

### Phase 3.B: Micro-Level Aggregation (Hierarchical Weighting)
The architectural bridge that translates the user's high-level cognitive decisions into the granular feature matrix required for SAW.

* **Equal Split Distribution (Default Policy):** Within each category, the calculated $W_{Macro}$ is distributed equally among its constituent features ($1/n$). 
* **Micro-BWM Overrides (Power User Specification):** The system permits the optional injection of local weights. A user can bypass the equal split by dictating specific intra-category preferences (e.g., stating that *Airbags* hold 80% of the *Safety* category's importance).
* **Absolute Weight Calculation:** The engine computes the final, global weight for every individual feature ($i$) belonging to category ($C$) using the multiplicative rule:
    * $$Absolute\_Weight_i = W_{Macro\_C} \times W_{Micro\_i}$$
    * *Constraint:* The sum of all absolute weights across the entire dataset remains strictly equal to $1.0$.

### Phase 4: Multicriteria Aggregation (Scoring via Simple Additive Weighting - SAW)
The crossover phase where the transformed data matrix and the absolute weights are integrated for final decision-making.

* **Weighted Sum Calculation:** The algorithm iterates over each valid alternative ($A_k$). The normalized score of each criterion ($x_{ki}$) is multiplied by its respective absolute weight ($Absolute\_Weight_i$), obtaining the total sum.
* **Fundamental Equation:** $$Score_{Global} = \sum_{i=1}^{n} (x_{ki} \times Absolute\_Weight_i)$$
* **Sorting / Ranking:** The final output is a dataset sorted in descending order by the $Score_{Global}$. The element positioned at Rank 1 represents the mathematical optimum of Cost-Benefit given the user's hierarchical preference profile and hard constraints.

### Phase 5: Sensitivity Analysis [Optional/Audit]
Post-processing auditing layer for risk validation in decision-making.

* **Weight Perturbation:** Application of a controlled variance (e.g., $\pm 5\%$ to $10\%$) to the weight of the main criterion (e.g., Price) to monitor the stability of the ranking.
* **Success Criterion:** If the vehicle ranked 1st remains in the same position after the perturbation of the matrix, the recommendation is classified as **robust** and of **low decisional risk**.