"""
=============================================================================
FRONT-END: STREAMLIT APP (CAR RECOMMENDATION ENGINE)
=============================================================================
Run this app by typing 'streamlit run app.py' in your terminal.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Importing the engines from our Backend
from src.step2_transformation import DataTransformer
from src.step3a_bwm_model import BWMCalculator
from src.step3b_hierarchical_bwm import HierarchicalAggregator
from src.step4_saw_aggregation import SAWCalculator

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="MCDA Recommender",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Smart Vehicle Recommender")
st.markdown("Based on **MCDA (Multiple Criteria Decision Analysis)** utilizing the **Hierarchical BWM + SAW** method.")

# We instantiate the aggregator early to read the YAML groups for the UI
aggregator = HierarchicalAggregator(config_name='step1_features_config.yaml')
feature_groups = aggregator.groups

# Raw CSV is used only for transparency views, so we load it once here.
data_path = Path(__file__).resolve().parent / 'data' / 'car_database.csv'
df_raw = pd.read_csv(data_path, delimiter=';')

# ==========================================
# 2. SIDEBAR (USER INPUTS)
# ==========================================
st.sidebar.header("💰 1. Budget Constraint")
budget = st.sidebar.slider("Maximum Budget ($)", min_value=50000, max_value=250000, value=120000, step=5000)

st.sidebar.divider()

# --- MACRO BWM ---
st.sidebar.header("🧠 2. Decision Profile (BWM)")
macro_categories = ["cost", "safety", "performance", "comfort", "aesthetics"]

best_cat = st.sidebar.selectbox("Which category is the MOST important?", macro_categories, index=0)
worst_cat = st.sidebar.selectbox("Which category is the LEAST important?", macro_categories, index=4)

st.sidebar.markdown("### BWM Evaluation (1 to 9)")
st.sidebar.caption("1 = Equal importance | 9 = Absolutely more important")

st.sidebar.markdown(f"**Comparing against the Best ({best_cat}):**")
bo_vector = {}
for cat in macro_categories:
    if cat != best_cat:
        bo_vector[cat] = st.sidebar.slider(f"{best_cat} vs {cat}", 1, 9, 3, key=f"bo_{cat}")

st.sidebar.markdown(f"**Comparing against the Worst ({worst_cat}):**")
ow_vector = {}
for cat in macro_categories:
    if cat != worst_cat:
        ow_vector[cat] = st.sidebar.slider(f"{cat} vs {worst_cat}", 1, 9, 3, key=f"ow_{cat}")

st.sidebar.divider()

# --- MICRO TUNING (HIERARCHICAL) ---
st.sidebar.header("⚙️ 3. Advanced: Micro Tuning")
st.sidebar.caption("By default, weights are distributed equally inside categories. Override them here.")

custom_micro_weights = {}

with st.sidebar.expander("🛠️ Customize Specific Features"):
    st.write("Distribute importance within specific categories:")
    
    for category, features in feature_groups.items():
        if st.checkbox(f"Customize '{category.capitalize()}'", key=f"chk_{category}"):
            st.markdown(f"**{category.capitalize()} Distribution:**")
            
            raw_weights = {}
            default_val = int(100 / len(features)) 
            
            for feat in features:
                raw_weights[feat] = st.slider(
                    feat.replace('_', ' ').title(), min_value=0, max_value=100, value=default_val, key=f"sld_{feat}"
                )
            
            total_score = sum(raw_weights.values())
            if total_score > 0:
                normalized_weights = {k: v / total_score for k, v in raw_weights.items()}
            else:
                normalized_weights = {k: 1.0 / len(features) for k in features}
                
            custom_micro_weights[category] = normalized_weights

st.sidebar.divider()
btn_calculate = st.sidebar.button("🚀 Generate Final Recommendation", use_container_width=True, type="primary")

# ==========================================
# 3. EXECUTION ENGINE (BACKEND)
# ==========================================
if btn_calculate:
    with st.spinner("Processing Mathematical Matrices and Calculating Weights..."):
        try:
            # Phase 2: ETL & Normalization (Reverted to your original working method)
            transformer = DataTransformer(config_name='step1_features_config.yaml', max_budget=budget)
            df_normalized = transformer.execute_pipeline()
            
            # Phase 3: BWM (Macro Weights)
            bwm = BWMCalculator(macro_categories)
            macro_weights, cr = bwm.calculate_weights(best_cat, worst_cat, bo_vector, ow_vector)
            
            # Phase 3.5: Hierarchical Multiplication
            absolute_weights = aggregator.generate_flat_weights(macro_weights, custom_micro_weights=custom_micro_weights)
            
            # Phase 4: SAW (Final Aggregation)
            saw = SAWCalculator()
            df_ranking = saw.calculate_ranking(df_normalized, absolute_weights)
            
            # --- STATE MANAGEMENT: SAVE TO SESSION ---
            st.session_state['df_ranking'] = df_ranking 
            st.session_state['df_normalized'] = df_normalized 
            st.session_state['macro_weights'] = macro_weights
            st.session_state['absolute_weights'] = absolute_weights
            st.session_state['feature_groups'] = feature_groups
            st.session_state['cr'] = cr
            st.session_state['has_results'] = True 
            
            # Celebration triggers only once, right after calculation
            st.balloons()
            
        except Exception as e:
            st.error(f"An error occurred in the rules engine: {e}")

# ==========================================
# 4. RESULTS DISPLAY (VIEW)
# ==========================================
# This block runs independently of the button, as long as data exists in the session.
if st.session_state.get('has_results', False):
    st.divider()
    
    # Retrieve variables from memory
    df_ranking = st.session_state['df_ranking']
    df_normalized = st.session_state['df_normalized']
    macro_weights = st.session_state['macro_weights']
    absolute_weights = st.session_state['absolute_weights']
    feature_groups = st.session_state['feature_groups']
    cr = st.session_state['cr']
    
    # Creating 3 tabs for a complete analytical journey
    tab_ranking, tab_transparency, tab_audit = st.tabs([
        "🏆 Top 5 Cars", 
        "🔍 Deep-Dive", 
        "📊 Audit (BWM)"
    ])
    
    # --- TAB 1: THE RANKING ---
    with tab_ranking:
        if cr < 0.1:
            st.success(f"**Perfect Consistency:** Your answers have high mathematical logic (CR: {cr:.3f})")
        elif cr < 0.2:
            st.warning(f"**Acceptable Consistency:** Minor deviations, but ranking is valid (CR: {cr:.3f})")
        else:
            st.error(f"**Logical Inconsistency (CR: {cr:.3f}):** BWM detected contradictions. Ranking may be distorted.")
        
        display_columns = ['car', 'version', 'Final_Score']
        
        # Ensure columns exist before displaying
        valid_columns = [col for col in display_columns if col in df_ranking.columns]
        df_top5 = df_ranking[valid_columns].head(5).copy()
        
        df_top5['Final_Score'] = df_top5['Final_Score'].apply(lambda x: f"{x:.4f}")
        df_top5.index += 1
        
        st.dataframe(df_top5, use_container_width=True)
        
    # --- TAB 2: THE 3-LEVEL DEEP DIVE ---
    with tab_transparency:
        st.header("🔍 Score Breakdown")
        
        top_5_indices = df_ranking.head(5).index
        
        # ---------------------------------------------------------
        # LEVEL 1: MACRO OVERVIEW (STACKED BAR FOR ALL 5 CARS)
        # ---------------------------------------------------------
        st.subheader("1. Macro Overview: Top 5 Comparison")
        st.write("Compare how the top contenders stack up against your main priorities.")
        
        overview_data = []
        for idx in top_5_indices:
            # 1. Capture the exact identity of the car
            target_car = df_ranking.loc[idx, 'car']
            target_version = df_ranking.loc[idx, 'version']
            car_label = f"#{list(top_5_indices).index(idx)+1} - {target_car}"

            # 2. SAFE LOOKUP: Find this exact car in the normalized matrix
            # This completely ignores Pandas Index and prevents the .loc[idx] crash
            row_norm = df_normalized[(df_normalized['car'] == target_car) & (df_normalized['version'] == target_version)]
            
            if not row_norm.empty:
                row_norm = row_norm.iloc[0] # Grab the first match as a Series
                
                for category, features in feature_groups.items():
                    macro_score = 0
                    for feat in features:
                        if feat in row_norm and feat in absolute_weights:
                            pts = row_norm[feat] * absolute_weights[feat]
                            if pts > 0:
                                macro_score += pts
                                
                    if macro_score > 0:
                        overview_data.append({
                            "Car": car_label,
                            "Category": category.capitalize(),
                            "Score Contribution": macro_score
                        })

        df_overview = pd.DataFrame(overview_data)
        if not df_overview.empty:
            fig_bar = px.bar(
                df_overview, x="Score Contribution", y="Car", color="Category",
                orientation='h', barmode='stack',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=10, l=0, r=0, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.divider()

        # ---------------------------------------------------------
        # LEVEL 2: MICRO OVERVIEW (SUNBURST CHART)
        # ---------------------------------------------------------
        st.subheader("2. Micro Deep-Dive: Individual Inspection")
        
        # The Dropdown Selector
        car_options = {
            f"#{i+1} - {df_ranking.loc[idx, 'car']} {df_ranking.loc[idx, 'version'][:15]}...": idx 
            for i, idx in enumerate(top_5_indices)
        }
        
        selected_car_label = st.selectbox("Select a car to inspect closely:", list(car_options.keys()))
        selected_idx = car_options[selected_car_label]
        
        # Identify the selected car
        row_ranking = df_ranking.loc[selected_idx]
        target_car = row_ranking['car']
        target_version = row_ranking['version']
        car_name = f"{target_car}"
        car_id = f"{selected_idx}-car"
        
        # SAFE LOOKUP: Pulling data robustly by matching string values
        matching_normalized_rows = df_normalized[
            (df_normalized['car'] == target_car) & (df_normalized['version'] == target_version)
        ]
        if matching_normalized_rows.empty:
            st.warning("Could not find the selected car in the normalized matrix. The micro chart cannot be built.")
            st.stop()

        row_normalized = matching_normalized_rows.iloc[0]
        
        # Safe fallback for raw data
        try:
            row_raw = df_raw[(df_raw['car'] == target_car) & (df_raw['version'] == target_version)].iloc[0]
        except Exception:
            row_raw = row_normalized
            
        sunburst_data = []
        total_car_score = 0
        
        for category, features in feature_groups.items():
            macro_score = 0
            category_name = category.capitalize()
            category_id = f"{car_id}-{category}"
            
            for feat in features:
                if feat in row_normalized and feat in absolute_weights:
                    # max() prevents negative/zero values from breaking Plotly rendering
                    micro_pts = max(row_normalized[feat] * absolute_weights[feat], 0.0001)
                    
                    macro_score += micro_pts
                    total_car_score += micro_pts
                    sunburst_data.append(dict(
                        id=f"{category_id}-{feat}", parent=category_id, 
                        name=feat.replace('_', ' ').title(), value=micro_pts
                    ))
            
            if macro_score > 0:
                sunburst_data.append(dict(
                    id=category_id, parent=car_id, 
                    name=category_name, value=macro_score
                ))

        sunburst_data.append(dict(id=car_id, parent="", name=car_name, value=total_car_score))

        df_sunburst = pd.DataFrame(sunburst_data)
        
        if not df_sunburst.empty:
            fig_sunburst = px.sunburst(
                df_sunburst, ids='id', names='name', parents='parent', values='value', 
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_sunburst.update_traces(textinfo="label+percent root")
            fig_sunburst.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=500)
            st.plotly_chart(fig_sunburst, use_container_width=True)
        else:
            st.error("Missing feature data in the normalized dataset to build the chart.")

        # ---------------------------------------------------------
        # LEVEL 3: RAW vs NORMALIZED TABLE
        # ---------------------------------------------------------
        st.subheader(f"3. Feature Transparency: {car_name}")
        st.write("Compare the raw CSV values against the normalized scores and final weights.")
        
        table_data = []
        
        for category, features in feature_groups.items():
            for feat in features:
                if feat in row_raw and feat in row_normalized:
                    raw_val = row_raw[feat]
                    norm_val = row_normalized[feat]
                    weight_applied = absolute_weights.get(feat, 0)
                    final_pts = norm_val * weight_applied
                    
                    table_data.append({
                        "Macro Category": category.capitalize(),
                        "Micro Feature": feat.replace('_', ' ').title(),
                        "CSV Raw Value": raw_val,
                        "Normalized (0 to 1)": f"{norm_val:.4f}",
                        "Final Points Added": f"{final_pts:.4f}"
                    })
                    
        df_specs = pd.DataFrame(table_data)
        st.dataframe(df_specs, use_container_width=True, hide_index=True)

    # --- TAB 3: THE MATHEMATICAL AUDIT ---
    with tab_audit:
        st.markdown("### 1. Macro Weights Calculated by BWM")
        st.caption("How the BWM engine interpreted your 1-to-9 sliders.")
        df_macro = pd.DataFrame(list(macro_weights.items()), columns=['Category', 'Weight'])
        df_macro = df_macro.sort_values(by='Weight', ascending=False)
        st.bar_chart(df_macro.set_index('Category'))
        
        st.markdown("### 2. Absolute Distribution Matrix (Macro * Micro)")
        st.caption("The exact flat weights injected into the SAW Calculator (Sum = 1.0).")
        st.json(absolute_weights)