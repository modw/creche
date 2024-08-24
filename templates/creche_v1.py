import streamlit as st
import pandas as pd
import numpy as np
import yaml
from utils.dateutils import months_to_str
from utils.plot import plot_trend
from utils.html import color_text
import tomllib

# Constants
CARE_TYPE_TO_KEY = {
    "Family Care": "family-care",
    "Center Based": "center-based",
}


with open(".streamlit/config.toml", "rb") as f:
    THEME_COLORS = tomllib.load(f)["theme"]


def ct(text: str, color: str = THEME_COLORS["primaryColor"]) -> str:
    """Convenience function to color text. Defaults to primary color of streamlit
    theme."""
    return color_text(text, color)


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
    return st.selectbox("I :blue[**live**] in:", states)


def get_cost_expectation(
    cost_multipliers: dict, user_state: str
) -> tuple[str, float]:
    """
    Get the cost expectation based on the cost multipliers and user state.

    Parameters:
    - cost_multipliers (dict): A dictionary containing the cost multipliers.
    - user_state (str): The user state for comparison.

    Returns:
    - cost_bracket (str): The selected cost expectation.
    - cost_multiplier (float): The corresponding cost multiplier.

    """
    cost_bracket = st.selectbox(
        f"Compared with all of :blue[**{user_state}**], I expect my :blue[**cost**] to be:",
        list(cost_multipliers.keys()),
        index=1,
    )
    return cost_bracket, cost_multipliers[cost_bracket]


def get_care_type():
    return st.selectbox(
        "The :blue[**type**] of daycare I'm interested in is:",
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
        cost_bracket, cost_multiplier = get_cost_expectation(
            cost_multipliers, user_state
        )

    with col3:
        care_type = get_care_type()

    care_data = load_data(config, CARE_TYPE_TO_KEY[care_type])
    return care_data, user_state, cost_multiplier, cost_bracket, care_type


# Daycare duration functions
def update_duration_write_container(container, start: int, end: int) -> None:
    """
    Update the duration write container with the selected start and end ages.

    Parameters:
    - container (Any): The container to write the duration.
    - start (int): The selected start age.
    - end (int): The selected end age.

    Returns:
    - None

    """
    container.markdown(
        f"I expect my child to be in daycare from \
            **{ct(months_to_str(start))}** \
                to **{ct(months_to_str(end))}** of age.",
        unsafe_allow_html=True,
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

    # with st.expander("Click here to change the duration of daycare"):
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
        update_duration_write_container(duration_write_container, start, end)

    return start, end


# Cost calculation functions
@st.cache_data
def compute_monthly_cost_df(
    tuition_dict: dict,
    age_config: dict,
    cost_multipliers: dict,
) -> pd.DataFrame:
    """
    Compute the monthly cost DataFrame based on the given parameters.

    Args:
        tuition_dict (dict): A dictionary containing the tuition costs for different age groups.
        age_config (dict): A dictionary containing the age configuration.
        cost_multipliers (dict): A dictionary containing the cost multiplier per bracket.

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

    months = np.arange(
        age_config["min-age"],
        age_config["max-age"] + 1,
        age_config["age-step"],
    )

    # create baseline month_to_cost array
    monthly_cost_arr = np.array([month_to_cost(month) for month in months])

    # iterate over cost multipliers and create a DataFrame
    cost_df = pd.DataFrame(
        {
            bracket: monthly_cost_arr * multiplier
            for bracket, multiplier in cost_multipliers.items()
        }
    )
    # divide by 12 to get monthly cost
    cost_df = (cost_df / 12).astype(int)

    return cost_df


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
    st.markdown(
        f"We're assuming the **{ct(cost)}** tuition cost per age group in **{ct(user_state)}** is:",
        unsafe_allow_html=True,
    )
    age_groups = state_data.index.to_list()
    cols = st.columns(len(age_groups))
    for col in cols[: len(age_groups)]:
        group = age_groups.pop(0)
        col.metric(group, f"${adjusted_tuition[group]:,}", None)


def display_cumulative_cost(
    cumulative_cost_df: pd.DataFrame,
    monthly_cost_df: pd.DataFrame,
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
    fig = plot_trend(
        cumulative_cost_df, monthly_cost_df, cost_multipliers, cost, start, end
    )
    st.plotly_chart(fig)


def display_summary_card(
    total_cost: float,
    avg_monthly_cost: float,
    duration_months: int,
    state: str,
    cost_bracket: str,
    care_type: str,
):
    """
    Display a summary card with key metrics.

    Parameters:
    - total_cost (float): The total cost of child care.
    - avg_monthly_cost (float): The average monthly cost of child care.
    - duration_months (int): The duration of child care in months.
    - state (str): The state of residence.
    - cost_bracket (str): The cost bracket of child care.
    - care_type (str): The type of child care.

    Returns:
    - None
    """
    st.markdown("#### Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Total Cost", value=f"${total_cost:,.0f}")
        st.metric(label="Duration", value=f"{duration_months} months")
        st.metric(label="State", value=state)

    with col2:
        st.metric(label="Avg. Monthly Cost", value=f"${avg_monthly_cost:,.0f}")
        st.metric(
            label="Cost Bracket",
            value=cost_bracket,
            help="(Based on your expectations)",
        )
        st.metric(label="Care Type", value=care_type)


def display_savings():
    """
    Display the potential savings for the user.
    """
    l, r = st.columns([2, 1])
    l.markdown("#### Ways to Save")
    r.markdown("#### Annual Savings")

    l, r = st.columns([2, 1])
    l.markdown(
        f"""
    <div class="savings-explainer">

    **Child and Dependent Care Tax Credit**
    
    The Child and Dependent Care Tax Credit allows you to claim 20% to 35% of up to \$3,000 \
    in childcare expenses for one child or up to \$6,000 for two or more children. \
    Depending on your income, the tax credit can save you between \$600 to \$2,100 per year.

    [IRS: Am I eligible to claim the Child and Dependent Care Credit?](https://www.irs.gov/help/ita/am-i-eligible-to-claim-the-child-and-dependent-care-credit)
    </div>
    """,
        unsafe_allow_html=True,
    )

    r.metric("$600 to", "$2,100")
    l, r = st.columns([2, 1])
    l.markdown(
        f"""
    <div class="savings-explainer">
    
    <b>Flexible Spending Accounts (FSAs)</b>
    
    A Dependent Care Flexible Spending Account (FSA) allows you to set aside\
     pre-tax dollars to pay for eligible childcare expenses. You can contribute\
     up to \$5,000 per year if you're single or married filing jointly, \
     and up to \$2,500 if you're married filing separately.

    [Investopedia: Dependent Care FSA](https://www.investopedia.com/articles/pf/09/dependent-care-fsa.asp)
    </div>
    """,
        unsafe_allow_html=True,
    )
    r.metric("$1,000 to", "$1,750")

    l, r = st.columns([2, 1])
    l.markdown(
        f"""
    <div class="savings-explainer">

    **State-Specific Programs**

    Many states offer childcare assistance programs, subsidies, or grants to\
         low- and middle-income families to help offset the cost of daycare.\
             Eligibility requirements and benefits vary by state.
             <br>
    [ChildCare.gov](https://www.childcare.gov/)<br>
    [ChildCare Aware: State by State Resources](https://www.childcareaware.org/resources/state-by-state-resource-map/)
    </div>
    """,
        unsafe_allow_html=True,
    )
    r.metric("0% to", "100%")


def display_references() -> None:
    """
    Display references and resources.
    """
    with st.expander("References and Resources"):
        st.markdown(
            """
        - [State Averages: ChildCare Aware of America](https://www.childcareaware.org/)
        - [Childcare Technical Assistance Network](https://childcareta.acf.hhs.gov/)
        - [National Database of Child Care Financial Assistance Programs](https://childcareta.acf.hhs.gov/consumer-education)
        - [Office of Child Care](https://www.acf.hhs.gov/occ)
        - [Tax Credits for Child Care Expenses](https://www.irs.gov/credits-deductions/individuals/child-and-dependent-care-credit)
        - [IRS: Am I eligible to claim the Child and Dependent Care Credit?](https://www.irs.gov/help/ita/am-i-eligible-to-claim-the-child-and-dependent-care-credit)
        - [Investopedia: Dependent Care FSA](https://www.investopedia.com/articles/pf/09/dependent-care-fsa.asp)
        - [ChildCare.gov](https://www.childcare.gov/)
        - [ChildCare Aware: State by State Resources](https://www.childcareaware.org/resources/state-by-state-resource-map/)
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
    st.markdown(
        "Use this tool to estimate the total cost of child care in your area.\
        We use state averages from [Child Care Aware](https://www.childcareaware.org/), along with assumptions about child care duration and\
             cost brackets, to provide an illustrative estimate.\
                \n*Always do your own research before making financial decisions*."
    )

    # Load CSS
    with open(config["style"]) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Get user input
    with st.container():
        st.markdown("##### Input")
        care_data, user_state, cost_multiplier, cost_bracket, care_type = (
            get_user_input(config)
        )

    state_data = care_data.loc[user_state]
    baseline_tuition = state_data.astype(int).to_dict()
    adjusted_tuition = (state_data * cost_multiplier).astype(int).to_dict()
    with st.container():
        display_tuition_metrics(
            state_data, adjusted_tuition, user_state, cost_bracket
        )

    # Calculate costs
    monthly_cost_df = compute_monthly_cost_df(
        baseline_tuition,
        config["parameters"]["ages"],
        config["parameters"]["cost-multipliers"],
    )

    cumulative_cost_df = cumulative_cost(monthly_cost_df)

    with st.container():
        st.write("#### Cost estimate over time")
        start, end = get_daycare_duration(config["parameters"]["ages"])

        # Display results
        display_cumulative_cost(
            cumulative_cost_df,
            monthly_cost_df,
            list(config["parameters"]["cost-multipliers"].keys()),
            cost_bracket,
            start,
            end,
        )

    with st.container():
        display_summary_card(
            total_cost=cumulative_cost_df.loc[end, cost_bracket]
            - cumulative_cost_df.loc[start, cost_bracket],
            avg_monthly_cost=monthly_cost_df.loc[
                start : end + 1, cost_bracket
            ].mean(),
            duration_months=end - start,
            state=user_state,
            cost_bracket=cost_bracket,
            care_type=care_type,
        )

    with st.container():
        display_savings()

    st.divider()
    display_references()


def load_config():
    # Load configuration
    with open("./config/config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)


if __name__ == "__main__":
    # Load config and run the application
    config = load_config()  # Implement this function to load your configuration
    run(config)
