import streamlit as st
import pandas as pd


def run(config: dict):
    ### Config
    # Set page config
    st.set_page_config(page_title="Child Care Cost Estimator", layout="wide")

    # Read CSS file
    style_path = config["style"]
    with open(style_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Load Data
    family_care_path = config["data"]["family-care"]
    family_care_df = pd.read_csv(family_care_path)

    center_based_path = config["data"]["center-based"]
    center_based_df = pd.read_csv(center_based_path)

    # Multipliers
    cost_multipliers = config["cost-multipliers"]

    ### Dash Layout
    col1, col2, col3 = st.columns(3)
    with col1:
        states = center_based_df['State'].unique()

        user_state = st.selectbox(
            "Select US State", states)  # Dropdown to select state

        # Use the selected_state variable in further processing
        st.write(user_state)

    with col2:
        # select price bracket
        # add italic text
        st.write(
            "Compared with <i>your</i> State, do you expect your costs to be:",
            unsafe_allow_html=True)
        # price_bracket = st.sel("Select Price Bracket", 0, 5, 2)

        cc1, cc2, cc3 = st.columns(3)  # Create 3 columns

        with cc1:
            a = st.button("High")
            st.write(a)

        with cc2:
            if st.button("Average"):
                st.write("Button 2 clicked")

        with cc3:
            if st.button("Low"):
                st.write("Button 3 clicked")
