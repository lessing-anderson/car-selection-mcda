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

### Phase 3: Preference Elicitation (Weighting via Best-Worst Method - BWM)
Module dedicated to the algorithmic extraction of the decision-maker's preference function, replacing the traditional AHP method to handle high-dimensionality matrices.

* **Best-Worst Identification:** The user defines, among the set of criteria, the Absolutely Best/Most Important (*Best*) and the Absolutely Worst/Least Important (*Worst*).
* **Preference Vectorization (Scale of 1 to 9):**
    * *Best-to-Others Vector:* Degree of superiority of the *Best* criterion over all others.
    * *Others-to-Worst Vector:* Degree of superiority of each criterion over the *Worst* criterion.
* **Minimax Optimization (*Weight Extraction*):** Mathematical processing of the vectors through a solver to minimize the inconsistency error. Generates a global vector of calibrated weights ($W$), ensuring that the mathematical sum is strictly equal to $1$ (or $100\%$).

### Phase 4: Multicriteria Aggregation (Scoring via Simple Additive Weighting - SAW)
The crossover phase where the transformed data and the assigned weights are integrated for decision-making.

* **Weighted Sum Calculation:** The algorithm iterates over each valid alternative ($A_i$). The normalized score of each criterion ($x_{ij}$) is multiplied by its respective global weight ($w_j$), obtaining the total sum.
* **Fundamental Equation:** $$Score_{Global} = \sum_{j=1}^{n} (x_{ij} \times w_j)$$
* **Sorting / Ranking:** The final output is a dataset sorted in descending order by the $Score_{Global}$. The element positioned at Rank 1 represents the mathematical optimum of Cost-Benefit given the parameterized constraints.

### Phase 5: Sensitivity Analysis [Optional/Audit]
Post-processing auditing layer for risk validation in decision-making.

* **Weight Perturbation:** Application of a controlled variance (e.g., $\pm 5\%$ to $10\%$) to the weight of the main criterion (e.g., Price) to monitor the stability of the ranking.
* **Success Criterion:** If the vehicle ranked 1st remains in the same position after the perturbation of the matrix, the recommendation is classified as **robust** and of **low decisional risk**.