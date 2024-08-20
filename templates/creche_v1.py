import streamlit as st
import streamlit_extras as stx
import pandas as pd
import numpy as np
from utils.dateutils import months_to_str
from utils.plot import plot_trend


# cache
@st.cache_data
def load_data(config: dict, dataset: str) -> pd.DataFrame:
    data = pd.read_csv(config["data"][dataset])
    return data.set_index("State").astype(int)


def get_user_input(config: dict):
    st.write("To start, please provide the following information:")
    # Load Data
    family_care_path = config["data"]["family-care"]
    family_care_df = pd.read_csv(family_care_path)

    center_based_path = config["data"]["center-based"]
    center_based_df = pd.read_csv(center_based_path)

    # Multipliers
    cost_multipliers = config["parameters"]["cost-multipliers"]

    ### Dash Layout
    col1, col2, col3 = st.columns(3)
    with col1:
        states = center_based_df["State"].unique()

        user_state = st.selectbox(
            "I **live** in:", states
        )  # Dropdown to select state

    with col2:
        global cost
        cost = st.selectbox(
            f"Compared with all of :blue[**{user_state}**], I expect my :orange[**cost**] to be:",
            cost_multipliers.keys(),
            index=1,
        )
        cost_multiplier = cost_multipliers[cost]

    with col3:
        care_type = st.selectbox(
            "The **type** of daycare I'm interested in is:",
            ["Family Care", "Center Based"],
        )

        care_type_to_key = {
            "Family Care": "family-care",
            "Center Based": "center-based",
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
        """
        )


def get_daycare_duration(age_config):

    # Initialize the slider value in session state if it doesn't exist
    if "start" not in st.session_state:
        st.session_state.start = age_config["default-age-start"]
    if "end" not in st.session_state:
        st.session_state.end = age_config["default-age-end"]

    # duration write containers
    duration_write_container = st.empty()

    def update_duration_write_container():
        duration_write_container.write(
            f"I expect my child to be in daycare from \
                **:blue[{months_to_str(st.session_state.start)}]**\
                     to **:red[{months_to_str(st.session_state.end)}]** of age."
        )

    update_duration_write_container()

    with st.expander("Click here to change the duration of daycare"):
        st.write(
            "Use the slider below to adjust the duration of daycare for your child."
        )

        start, end = st.slider(
            f"Time in daycare",
            age_config["min-age"],
            age_config["max-age"],
            (age_config["default-age-start"], age_config["default-age-end"]),
            step=age_config["age-step"],
            format="%d months",
            label_visibility="visible",
        )

        # Update the session state when the slider changes
        if start != st.session_state.start:
            st.session_state.start = start
            update_duration_write_container()
        if end != st.session_state.end:
            st.session_state.end = end
            update_duration_write_container()

    return start, end


@st.cache_data
def compute_monthly_cost_df(
    start, end, tuition_dict, age_config, default_multiplier
):

    def month_to_cost(month):
        if month < 12:
            return tuition_dict["Infant"]
        elif month < 48:
            return tuition_dict["Toddler"]
        else:
            return tuition_dict["4-Year-Old"]

    cost_df = pd.DataFrame(
        index=np.arange(
            age_config["min-age"],
            age_config["max-age"] + 1,
            age_config["age-step"],
        ),
        columns=[default_multiplier],
    )
    cost_df[default_multiplier] = cost_df.index.map(month_to_cost)
    cost_df = (cost_df / 12).astype(int)

    return cost_df


def tuition_metrics(state_data, adjusted_tuition, user_state):
    # Display tuition per age group
    st.write(
        f"We're assuming the :orange[**{cost}**] tuition bracket per age group in :blue[**{user_state}**] is:"
    )
    age_groups = state_data.index.to_list()
    cols = st.columns(len(age_groups) * 2)
    for col in cols[: len(age_groups)]:
        group = age_groups.pop(0)
        col.metric(
            group,
            f"${adjusted_tuition[group]:,}",
            None,
        )


@st.cache_data
def cumulative_cost(monthly_cost_df):
    return monthly_cost_df.cumsum()


def run(config: dict):
    """
    Run the Childcare Cost Estimator streamlit app.

    Parameters:
    - config (dict): A dictionary containing the configuration settings.

    Returns:
    - None
    """
    # Load parameters
    cost_multiplier_dict = config["parameters"]["cost-multipliers"]
    cost_multipliers = list(cost_multiplier_dict.keys())
    default_multiplier = config["parameters"]["default-multiplier"]
    age_config = config["parameters"]["ages"]

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

    # Get user input

    care_data, user_state, cost_multiplier = get_user_input(config)
    # state_data is of the form:
    state_data = care_data.loc[user_state]
    # Adjusted tuition
    adjusted_tuition = (state_data * cost_multiplier).astype(int).to_dict()

    tuition_metrics(state_data, adjusted_tuition, user_state)
    start, end = get_daycare_duration(age_config)

    # Get cost dataframe
    monthly_cost_df = compute_monthly_cost_df(
        start, end, adjusted_tuition, age_config, default_multiplier
    )

    for bracket, multiplier in cost_multiplier_dict.items():
        monthly_cost_df[bracket] = (
            monthly_cost_df[default_multiplier] * multiplier
        )

    # Cumulative cost
    cumulative_cost_df = cumulative_cost(monthly_cost_df)

    # Plot the cumulative monthly cost in the first column
    st.write("The cumulative monthly cost of daycare is:")

    fig = plot_trend(
        cumulative_cost_df,
        cost_multipliers,
        cost,
        start,
        end,
    )
    st.plotly_chart(fig)

    # Add a total cost card on the second column
    total_cost = (
        cumulative_cost_df.loc[end, cost] - cumulative_cost_df.loc[start, cost]
    )
    st.metric(
        f"Estimated total cost of daycare from {months_to_str(start)} to {months_to_str(end)}",
        f"${total_cost:,.0f}",
    )

    # add horizontal line
    st.divider()
    references()
