import streamlit as st
import pandas as pd


# cache
@st.cache_data
def load_data(config: dict, dataset: str) -> pd.DataFrame:
    data = pd.read_csv(config["data"][dataset])
    return data


def get_user_input(config: dict):
    st.write("To start, please provide the following information:")
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
            "I **live** in:", states)  # Dropdown to select state

    with col2:
        cost = st.selectbox(
            f"Compared with all of :blue[**{user_state}**], I expect my **cost** to be:",
            ["High", "Average", "Low"],
            index=1)
        cost_to_key = {"High": "high", "Average": "mid", "Low": "low"}
        cost_multiplier = cost_multipliers[cost_to_key[cost]]

    with col3:
        care_type = st.selectbox(
            "The **type** of daycare I'm interested in is:",
            ["Family Care", "Center Based"])

        care_type_to_key = {
            "Family Care": "family-care",
            "Center Based": "center-based"
        }

    care_data = load_data(config, care_type_to_key[care_type])
    return care_data, user_state, cost_multiplier


def references():
    # horizontal bar

    with st.expander("References and Resources"):
        st.markdown(
            """
        - [State Averages: Child Care Aware of America](https://www.childcareaware.org/)
        - [Childcare Technical Assistance Network](https://childcareta.acf.hhs.gov/)
        - [National Database of Child Care Financial Assistance Programs](https://childcareta.acf.hhs.gov/consumer-education)
        - [Office of Child Care](https://www.acf.hhs.gov/occ)
        - [Tax Credits for Child Care Expenses -](https://www.irs.gov/credits-deductions/individuals/child-and-dependent-care-credit)
        """)


def run(config: dict):
    ### Config
    # Set page config
    st.set_page_config(page_title="Child Care Cost Estimator", layout="wide")
    st.title("Childcare Cost Estimator")

    st.write(
        "Use this tool to estimate the total cost of child care in your area. This tool uses data, along with assumptions about child care duration and cost brackets, to provide an estimate of the total cost of child care in your area."
    )

    # Read CSS file
    style_path = config["style"]
    with open(style_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    care_data, user_state, cost_multiplier = get_user_input(config)
    state_data = care_data[care_data['State'] == user_state]
    st.dataframe(care_data.loc[care_data['State'] == user_state])

    # cost basics and totals

    # cumulative plots assuming start and end ages
    references()
