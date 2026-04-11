# ADR 002: Adoption of Hierarchical BWM for Weight Aggregation

**Date:** April 11, 2026  
**Status:** Accepted  
**Project Context:** Decision Support System for Zero-Kilometer Vehicle Selection

## 1. Context and Problem

Following the implementation of ADR 001 (Adoption of BWM + SAW), testing revealed a critical cognitive and mathematical bottleneck. While BWM drastically reduces the required pairwise comparisons to 2n - 3, applying this directly to a dataset with approximately 25 to 30 active variance variables still demands over 50 manual inputs from the user. 

Evaluating 28 disparate criteria (ranging from engine torque to fog lights) sequentially against a single "Best" or "Worst" anchor causes severe cognitive fatigue. Invariably, this leads to logical contradictions in user inputs, causing the Consistency Ratio (CR) to exceed the acceptable threshold (CR > 0.2). When the CR fails, the resulting SAW ranking loses its mathematical validity.

## 2. Considered Alternatives

* **Option A: Standard Linear BWM on the full feature set**
    * *Verdict:* **Rejected**. Forces the user to evaluate ~28 variables on a 1-to-9 scale. Guaranteed cognitive overload and high probability of CR explosion, rendering the system unusable for a standard consumer.
* **Option B: Dimensionality Reduction (PCA) or Feature Elimination**
    * *Verdict:* **Rejected**. While algorithmically sound for Machine Learning, applying PCA creates "black-box" principal components, completely destroying the explainability constraint required for this system. Dropping minor features artificially prevents users from selecting cars based on specific granular preferences (e.g., presence of a rear-view camera).
* **Option C: Hierarchical BWM (Two-Tier Aggregation)**
    * *Verdict:* **Accepted**. This approach structures the decision into two distinct layers: Macro and Micro. It bridges the gap between human cognitive limits and high-dimensional matrices without sacrificing explainability or granularity.

## 3. Architectural Decision

We will implement a **Two-Tier Hierarchical BWM** architecture orchestrated by a new backend component (`HierarchicalAggregator`):

1. **Macro Layer:** The ~30 features will be logically grouped into 5 to 7 Macro Categories (e.g., Cost, Safety, Performance) defined in the Data Contract. The user performs the standard BWM elicitation *only* on these macro categories, ensuring a swift UX and a highly stable Consistency Ratio.
2. **Micro Layer:** Within each category, the macro weight is distributed among its constituent features. By default, an equal-weight split (1/n) is applied. However, the architecture permits optional "Micro-BWM" overrides, allowing the user to heavily weight a specific feature (e.g., Airbags) within its parent category. 
3. **Absolute Weights:** The final weight vector injected into the SAW algorithm is calculated mathematically as: `Absolute_Weight_i = Macro_Weight_C * Micro_Weight_i`.

## 4. Consequences and Trade-offs

### Positives
* **CR Stability & UX:** Drastically reduces front-end inputs (from ~50 to roughly 8), virtually eliminating cognitive fatigue and guaranteeing mathematically consistent vectors.
* **Preservation of Granularity:** Retains the system's ability to evaluate dozens of minor vehicle features without penalizing the user's decision-making process.
* **Modularity:** The Aggregation module acts as a clean bridge, requiring no changes to the core `BWMCalculator` or `SAWCalculator` engines.

### Points of Attention (Risks and Mitigations)
* **Data Contract Coupling:** The mathematical aggregation relies entirely on the logical grouping of features. 
    * *Mitigation:* The mapping of which column belongs to which Macro Category must be strictly governed by the dictionary. Any new column added to the database must be mapped to a category, or it will be ignored by the SAW engine.