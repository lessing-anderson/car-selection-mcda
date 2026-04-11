# ADR 001: Analytical Model Choice for Vehicle Recommendation (MCDA)

**Date:** April 10, 2026  
**Status:** Accepted  
**Project Context:** Decision Support System for Zero-Kilometer Vehicle Selection

## 1. Context and Problem

The core requirement of the system is to rank a dataset of zero-kilometer vehicles based on user preferences across a high-dimensional criteria space (approx. 50 variables). We needed an algorithmic engine capable of translating subjective user preferences into an objective mathematical ranking.

The primary challenge is the cognitive load and mathematical complexity of calculating weights for 50 conflicting variables (e.g., price, safety, comfort items) without losing logical consistency.

## 2. Considered Alternatives

* **Option A: Analytic Hierarchy Process (AHP)**
    * *Verdict:* **Rejected**. AHP requires full pairwise comparisons across all criteria. For $n=50$ variables, the formula $n(n-1)/2$ results in 1,225 comparisons. This is mathematically unfeasible, induces severe user fatigue, and guarantees that the Consistency Ratio (CR) will fail.
* **Option B: Predictive Machine Learning (Regression Models)**
    * *Verdict:* **Rejected**. Training a regressor to find undervalued cars ("bargains") does not work for zero-kilometer vehicles. The primary market is strictly price-controlled by manufacturers, meaning there is no market variance or wear-and-tear variables to exploit.
* **Option C: Simple Clustering ("Bag of Features" + SAW)**
    * *Verdict:* **Rejected**. Grouping dozens of comfort items into a single package and assigning a macro weight to the package destroys the variance and sensitivity of the model. A high value-added item (e.g., Sunroof) would incorrectly hold the same weight in the final calculation as a trivial item (e.g., Courtesy light).
* **Option D: Best-Worst Method (BWM) + Simple Additive Weighting (SAW)**
    * *Verdict:* **Accepted**. BWM solves the dimensionality issue by comparing variables only against the "Best" and "Worst" criteria, reducing the required comparisons from 1,225 to just 97 ($2n - 3$). SAW provides a computationally light, highly transparent ("white-box") method for aggregating these weights with the normalized data.

## 3. Architectural Decision

We will implement **BWM (Best-Worst Method)** for the preference elicitation and weight extraction phase, coupled with **SAW (Simple Additive Weighting)** for the final multicriteria aggregation and ranking.

## 4. Consequences and Trade-offs

### Positives
* **Scalability:** Solves the $O(n^2)$ complexity problem of AHP, allowing the system to easily handle 50+ variables.
* **Transparency:** The SAW aggregation is fully explainable. We can pinpoint exactly which criteria caused a vehicle to gain or lose rank.
* **Computational Efficiency:** The optimization problem for BWM can be solved instantly on standard CPUs without the need for ML infrastructure.

### Points of Attention (Risks and Mitigations)
* **The Compensatory Nature of SAW:** SAW allows a terrible score in one criterion to be offset by an excellent score in another. 
    * *Mitigation:* This architectural limitation of SAW will be mitigated upstream in the data ingestion pipeline (documented separately) by applying strict Boolean *Hard Constraints* to eliminate fundamentally flawed vehicles before they reach the SAW engine.