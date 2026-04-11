# 🚗 Decision Support System for Vehicle Selection (Hybrid MCDA)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Processing-green.svg)](https://pandas.pydata.org/)
[![MCDA](https://img.shields.io/badge/MCDA-BWM%20%2B%20SAW-orange.svg)]()

An analytical recommendation engine developed to solve the multi-objective optimization problem of purchasing a zero-kilometer vehicle. This project replaces subjective choice with a mathematical **Operations Research** model, utilizing Multi-Criteria Decision Analysis (MCDA).

---

## 📌 The Problem

Choosing a vehicle involves dozens of conflicting variables (Cost vs. Horsepower; Cost vs. Equipment). Traditional decision-making models (like simple mental weighting or "intuition") fail when faced with high data dimensionality (e.g., comparing 50 features across 30 different cars).

Additionally, traditional Predictive Machine Learning techniques fail in this specific scenario (zero-km cars) due to strict market efficiency (fixed manufacturer prices), which makes the search for "anomalies" or "bargains" via regression unfeasible.

## 💡 The Solution (MCDA Architecture)

The solution was developed as a **Hybrid Pipeline** that combines rigorous Feature Engineering with the state-of-the-art in weight extraction:

1. **Ingestion & Boolean Filters:** Dataset cleaning (removal of zero-variance features) and application of Hard Constraints (e.g., "Only automatic transmissions").
2. **Non-Linear Utility Engineering:** Application of discrete normalization for variables with non-proportional impact. (e.g., The utility leap from 0 to 2 airbags is strictly greater than the leap from 4 to 6 airbags).
3. **Best-Worst Method (BWM):** Mathematical elicitation of user preferences, calculating the exact weight vector through minimax optimization (replacing the impractical AHP for high dimensionality).
4. **Simple Additive Weighting (SAW):** Final aggregation of the normalized scores against the BWM weight matrix, ranking the vehicles by the mathematical optimum of Cost-Benefit.

> **📄 For in-depth mathematical details regarding utility functions and model architecture, please refer to the [Technical Specification (TECH_SPEC.md)](docs/TECH_SPEC.md).**

---

## 🛠️ Tech Stack

* **Language:** Python 3.13.3
* **Data Processing & Transformation:** `pandas`, `numpy`
* **Optimization (BWM Solver):** `scipy.optimize`
* **Environment:** `pyenv` / `pyenv-virtualenv`

---

## 🚀 How to Run Locally

**1. Clone the repository**
```bash
git clone https://github.com/lessing-anderson/car-selection-mcda.git
cd car-selection-mcda
```

**2. Set up the virtual environment**
```bash
pyenv install 3.13.3
pyenv virtualenv 3.13.3 car-selection-mcda

```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Execute the Pipeline**

```bash
python src/main.py
```

## 📊 Directory Structure

```text
car-selection-mcda/
│
├── docs/                      # Detailed documentation
│   ├── ADR/                   # Architecture Decision Records
│   ├── FEATURE-ENGINEERING.md # Feature Engineering & Data Mapping Specification
│   └── TECH-SPEC.md           # Technical Specification
├── notebooks/                 # Prototyping Notebooks
├── src/                       # Pipeline Source Code
│   ├── step1_features_config.yaml   # Feature Engineering Config
│   ├── step2_transformation.py      # Cleaning and Normalization (Phase 2)
│   ├── step3_bwm_model.py           # BWM Weight Calculation (Phase 3)
│   └── step4_saw_aggregation.py     # Final Scoring and Ranking (Phase 4)
├── data/                      # Input dataset
│   └── car_database.csv       
├── requirements.txt           # Python dependencies
└── README.md                  # This document
```

## 🎯 Roadmap

- [ ] Implement sensitivity analysis via matrix perturbation (+/- 5% on macro weights).
- [ ] Incorporate the PROMETHEE II outranking method to entirely avoid the compensatory effect of the SAW algorithm.
- [ ] Create an interactive web interface using Streamlit for visual input of Best and Worst criteria.


------------------
Project developed as a demonstration of analytical modeling and data-driven decision making.