import streamlit as st
import pandas as pd
import numpy as np
from utils.dateutils import months_to_str
from utils.plot import plot_trend

# Constants
CARE_TYPE_TO_KEY = {
    "Family Care": "family-care",
    "Center Based": "center-based",
}


# Data loading
@st.cache_data
def load_data(config: dict, dataset: str) -> pd.DataFrame:
    data = pd.read_csv(config["data"][dataset])
    return data.set_index("State").astype(int)


# User input functions
def get_user_state(states: list[str]) -> str:
    """
    Returns the selected state from a dropdown menu.

    Parameters:
    - states (list): A list of available states.

    Returns:
    - str: The selected state.

    Example:
    >>> states = ["California", "New York", "Texas"]
    >>> get_user_state(states)
    'California'
    """
    return st.selectbox("I **live** in:", states)


def get_cost_expectation(
    cost_multipliers: dict, user_state: str
) -> tuple[str, float]:
    """
    Get the cost expectation based on the cost multipliers and user state.

    Parameters:
    - cost_multipliers (dict): A dictionary containing the cost multipliers.
    - user_state (str): The user state for comparison.

    Returns:
    - cost (str): The selected cost expectation.
    - cost_multiplier (float): The corresponding cost multiplier.

    """
    cost = st.selectbox(
        f"Compared with all of :blue[**{user_state}**], I expect my :orange[**cost**] to be:",
        list(cost_multipliers.keys()),
        index=1,
    )
    return cost, cost_multipliers[cost]


def get_care_type():
    return st.selectbox(
        "The **type** of daycare I'm interested in is:",
        ["Family Care", "Center Based"],
    )


def get_user_input(config: dict) -> tuple[pd.DataFrame, str, float, str]:
    """
    Get user input for child care estimation.

    Parameters:
    - config (dict): The configuration dictionary.

    Returns:
    - care_data (pd.DataFrame): The child care data.
    - user_state (str): The selected user state.
    - cost_multiplier (float): The selected cost multiplier.
    - cost (str): The selected cost expectation.

    """
    family_care_df = pd.read_csv(config["data"]["family-care"])
    center_based_df = pd.read_csv(config["data"]["center-based"])
    cost_multipliers = config["parameters"]["cost-multipliers"]

    col1, col2, col3 = st.columns(3)
    with col1:
        states = center_based_df["State"].unique()
        user_state = get_user_state(states)

    with col2:
        cost, cost_multiplier = get_cost_expectation(
            cost_multipliers, user_state
        )

    with col3:
        care_type = get_care_type()

    care_data = load_data(config, CARE_TYPE_TO_KEY[care_type])
    return care_data, user_state, cost_multiplier, cost


# Daycare duration functions
def update_duration_write_container(
    container: st.container, start: int, end: int
) -> None:
    """
    Update the duration write container with the selected start and end ages.

    Parameters:
    - container (Any): The container to write the duration.
    - start (int): The selected start age.
    - end (int): The selected end age.

    Returns:
    - None

    """
    container.write(
        f"I expect my child to be in daycare from \
            **:blue[{months_to_str(start)}]** to **:red[{months_to_str(end)}]** of age."
    )


def get_daycare_duration(age_config: dict) -> tuple[int, int]:
    """
    Get the duration of daycare for a child.

    Parameters:
    - age_config (dict): The configuration dictionary for age settings.

    Returns:
    - tuple[int, int]: The selected start and end ages for daycare.

    """
    if "start" not in st.session_state:
        st.session_state.start = age_config["default-age-start"]
    if "end" not in st.session_state:
        st.session_state.end = age_config["default-age-end"]

    duration_write_container = st.empty()
    update_duration_write_container(
        duration_write_container, st.session_state.start, st.session_state.end
    )

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

        if start != st.session_state.start or end != st.session_state.end:
            st.session_state.start, st.session_state.end = start, end
            update_duration_write_container(
                duration_write_container, start, end
            )

    return start, end


# Cost calculation functions
@st.cache_data
def compute_monthly_cost_df(
    start: int,
    end: int,
    tuition_dict: dict,
    age_config: dict,
    default_multiplier: str,
) -> pd.DataFrame:
    """
    Compute the monthly cost DataFrame based on the given parameters.

    Args:
        start (int): The starting month.
        end (int): The ending month.
        tuition_dict (dict): A dictionary containing the tuition costs for different age groups.
        age_config (dict): A dictionary containing the age configuration.
        default_multiplier (str): The default multiplier.

    Returns:
        pd.DataFrame: The computed monthly cost DataFrame.
    """

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
    return (cost_df / 12).astype(int)


@st.cache_data
def cumulative_cost(monthly_cost_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the cumulative cost of a monthly cost DataFrame.

    Args:
        monthly_cost_df (pd.DataFrame): The DataFrame containing the monthly cost data.

    Returns:
        pd.DataFrame: The DataFrame with the cumulative cost calculated.
    """

    return monthly_cost_df.cumsum()


# Display functions
def display_tuition_metrics(
    state_data: pd.DataFrame, adjusted_tuition: dict, user_state: str, cost: str
) -> None:
    """
    Display the tuition metrics for different age groups in a given state.

    Parameters:
    - state_data (pandas.DataFrame): The data containing the tuition metrics for different age groups.
    - adjusted_tuition (dict): A dictionary containing the adjusted tuition values for each age group.
    - user_state (str): The name of the state for which the tuition metrics are being displayed.
    - cost (str): The tuition bracket per age group in the state.

    Returns:
    None
    """
    st.write(
        f"We're assuming the :orange[**{cost}**] tuition bracket per age group in :blue[**{user_state}**] is:"
    )
    age_groups = state_data.index.to_list()
    cols = st.columns(len(age_groups) * 2)
    for col in cols[: len(age_groups)]:
        group = age_groups.pop(0)
        col.metric(group, f"${adjusted_tuition[group]:,}", None)


def display_cumulative_cost(
    cumulative_cost_df: pd.DataFrame,
    cost_multipliers: dict,
    cost: str,
    start: int,
    end: int,
) -> None:
    """
    Display the cumulative monthly cost of daycare.

    Parameters:
        cumulative_cost_df (pd.DataFrame): The DataFrame containing the cumulative cost data.
        cost_multipliers (dict): Dictionary with cost multipliers per cost bracket.
        cost (str): The specific cost bracket to display.
        start (int): The starting month.
        end (int): The ending month.

    Returns:
        None
    """
    st.write("The cumulative monthly cost of daycare is:")
    fig = plot_trend(cumulative_cost_df, cost_multipliers, cost, start, end)
    st.plotly_chart(fig)


def display_total_cost(
    cumulative_cost_df: pd.DataFrame, cost: str, start: int, end: int
) -> None:
    """
    Display the estimated total cost of daycare.

    Parameters:
    - cumulative_cost_df (pd.DataFrame): The DataFrame containing the cumulative cost data.
    - cost (str): The specific cost bracket to display.
    - start (int): The starting month.
    - end (int): The ending month.

    Returns:
    - None
    """
    total_cost = (
        cumulative_cost_df.loc[end, cost] - cumulative_cost_df.loc[start, cost]
    )
    st.metric(
        f"Estimated total cost of daycare from {months_to_str(start)} to {months_to_str(end)}",
        f"${total_cost:,.0f}",
    )


def display_references() -> None:
    """
    Display references and resources.
    """
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


# Main application function
def run(config: dict):
    """
    Run the child care cost estimator application.

    Parameters:
    - config (dict): The configuration dictionary.

    Returns:
    - None
    """
    st.set_page_config(page_title="Child Care Cost Estimator", layout="wide")
    st.title("Childcare Cost Estimator")
    st.write(
        "Use this tool to estimate the total cost of child care in your area. This tool uses data, along with assumptions about child care duration and cost brackets, to provide an estimate of the total cost of child care in your area."
    )

    # Load CSS
    with open(config["style"]) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Get user input
    care_data, user_state, cost_multiplier, cost = get_user_input(config)
    state_data = care_data.loc[user_state]
    adjusted_tuition = (state_data * cost_multiplier).astype(int).to_dict()

    display_tuition_metrics(state_data, adjusted_tuition, user_state, cost)

    start, end = get_daycare_duration(config["parameters"]["ages"])

    # Calculate costs
    monthly_cost_df = compute_monthly_cost_df(
        start,
        end,
        adjusted_tuition,
        config["parameters"]["ages"],
        config["parameters"]["default-multiplier"],
    )
    for bracket, multiplier in config["parameters"]["cost-multipliers"].items():
        monthly_cost_df[bracket] = (
            monthly_cost_df[config["parameters"]["default-multiplier"]]
            * multiplier
        )

    cumulative_cost_df = cumulative_cost(monthly_cost_df)

    # Display results
    display_cumulative_cost(
        cumulative_cost_df,
        list(config["parameters"]["cost-multipliers"].keys()),
        cost,
        start,
        end,
    )
    display_total_cost(cumulative_cost_df, cost, start, end)

    st.divider()
    display_references()


if __name__ == "__main__":
    # Load config and run the application
    config = load_config()  # Implement this function to load your configuration
    run(config)
