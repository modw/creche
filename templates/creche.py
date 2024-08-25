import streamlit as st
import pandas as pd
import numpy as np
import yaml
from dataclasses import dataclass
from typing import Dict, Union
from utils.dateutils import months_to_str
from utils.plot import plot_trend
from utils.html import color_text
from main import AppConfig
import tomllib

# Constants
CARE_TYPE_TO_KEY = {
    "Family Care": "family-care",
    "Center Based": "center-based",
}

with open(".streamlit/config.toml", "rb") as f:
    THEME_COLORS = tomllib.load(f)["theme"]


def ct(text: str, color: str = THEME_COLORS["primaryColor"]) -> str:
    """Convenience function to color text. Defaults to primary color of streamlit theme."""
    return color_text(text, color)


@dataclass
class CostData:
    infant: float
    toddler: float
    preschool: float


class ChildcareCostEstimator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.default_data = self.process_default_data()
        self.user_state = None
        self.cost_multiplier = None
        self.cost_bracket = None
        self.care_type = None
        self.cost_data: Union[CostData, None] = None
        self.use_default_data = True
        self.start_age = None
        self.end_age = None
        self.user_bracket = None
        self.user_multiplier = 1.0

    def process_default_data(self):
        default_data = {
            care_type: {
                state: CostData(
                    infant=data["Infant"],
                    toddler=data["Toddler"],
                    preschool=data["4-Year-Old"],
                )
                for state, data in pd.read_csv(self.config.data[care_type])
                .set_index("State")
                .to_dict("index")
                .items()
            }
            for care_type in ["family-care", "center-based"]
        }
        return default_data

    def get_user_choice(self):

        self.use_default_data = (
            st.selectbox(
                "Do you want to use state averages or input your own data?",
                ("Use state averages", "Input my own data"),
            )
            == "Use state averages"
        )

    def get_user_input(self):
        states = list(self.default_data["center-based"].keys())
        col1, col2, col3 = st.columns(3)
        with col1:
            self.user_state = st.selectbox("I live in:", states)
        with col2:
            self.care_type = st.selectbox(
                "The type of daycare I'm interested in is:",
                list(CARE_TYPE_TO_KEY.keys()),
            )
        with col3:
            self.cost_bracket, self.cost_multiplier = (
                self.get_cost_expectation()
            )

        self.get_user_choice()

        if not self.use_default_data:
            self.user_bracket = "User Data"
            self.get_user_cost_data()
        else:
            self.cost_data = self.default_data[
                CARE_TYPE_TO_KEY[self.care_type]
            ][self.user_state]
            self.user_bracket = self.cost_bracket
            self.user_multiplier = self.cost_multiplier

    def get_cost_expectation(self):
        cost_multipliers = self.config.parameters["cost-multipliers"]
        cost_bracket = st.selectbox(
            f"Compared with all of **{self.user_state}**, I expect my **cost** to be:",
            list(cost_multipliers.keys()),
            index=1,
        )
        return cost_bracket, cost_multipliers[cost_bracket]

    def get_user_cost_data(self):
        st.subheader("Enter your cost data")
        col1, col2, col3 = st.columns(3)
        with col1:
            infant_cost = st.number_input(
                "Infant care cost (annual)",
                min_value=0.0,
                step=100.0,
                help="Infant: 0-12 months",
            )
        with col2:
            toddler_cost = st.number_input(
                "Toddler care cost (annual)",
                min_value=0.0,
                step=100.0,
                help="Toddler: 1-4 years",
            )
        with col3:
            preschool_cost = st.number_input(
                "Preschool care cost (annual)",
                min_value=0.0,
                step=100.0,
                help="Preschool: 4+ years",
            )
        self.cost_data = CostData(infant_cost, toddler_cost, preschool_cost)

    def get_daycare_duration(self):
        age_config = self.config.parameters["ages"]
        duration_write_container = st.empty()

        def update_duration_write_container(start: int, end: int) -> None:
            duration_write_container.markdown(
                f"I expect my child to be in daycare from \
                    **{ct(months_to_str(start))}** \
                        to **{ct(months_to_str(end))}** of age.",
                unsafe_allow_html=True,
            )

        self.start_age, self.end_age = st.slider(
            f"Time in daycare",
            age_config["min-age"],
            age_config["max-age"],
            (age_config["default-age-start"], age_config["default-age-end"]),
            step=age_config["age-step"],
            format="%d months",
            label_visibility="visible",
        )
        update_duration_write_container(self.start_age, self.end_age)

    def calculate_costs(self):
        def month_to_cost(month):
            if month < 12:
                return self.cost_data.infant
            elif month < 48:
                return self.cost_data.toddler
            else:
                return self.cost_data.preschool

        age_config = self.config.parameters["ages"]
        months = np.arange(
            age_config["min-age"],
            age_config["max-age"] + 1,
            age_config["age-step"],
        )

        monthly_cost_arr = np.array([month_to_cost(month) for month in months])

        if self.use_default_data:
            cost_multipliers = self.config.parameters["cost-multipliers"]
        else:
            cost_multipliers = {
                "User Data": 1,
            }

        self.monthly_cost_df = pd.DataFrame(
            {
                bracket: monthly_cost_arr * multiplier
                for bracket, multiplier in cost_multipliers.items()
            }
        )
        self.monthly_cost_df = (self.monthly_cost_df / 12).astype(int)
        self.cumulative_cost_df = self.monthly_cost_df.cumsum()

    def display_tuition_metrics(self):
        st.markdown(
            f"We're assuming the **{ct(self.cost_bracket)}** tuition cost per age group in **{ct(self.user_state)}** is:",
            unsafe_allow_html=True,
        )
        adjusted_tuition = {
            "Infant": self.cost_data.infant * self.user_multiplier,
            "Toddler": self.cost_data.toddler * self.user_multiplier,
            "Preschool": self.cost_data.preschool * self.user_multiplier,
        }
        cols = st.columns(3)
        for col, (group, cost) in zip(cols, adjusted_tuition.items()):
            col.metric(group, f"${cost:,.0f}", None)

    def display_cumulative_cost(self, columns_included=None):
        if columns_included is None:
            columns_included = list(self.monthly_cost_df.columns)

        st.write("#### Cost estimate over time")
        fig = plot_trend(
            cumulative_data=self.cumulative_cost_df,
            monthly_data=self.monthly_cost_df,
            columns_included=columns_included,
            column_highlight=self.user_bracket,
            left=self.start_age,
            right=self.end_age,
        )
        st.plotly_chart(fig)

    def display_summary_card(self):
        total_cost = (
            self.cumulative_cost_df.loc[self.end_age, self.user_bracket]
            - self.cumulative_cost_df.loc[self.start_age, self.user_bracket]
        )
        avg_monthly_cost = self.monthly_cost_df.loc[
            self.start_age : self.end_age + 1, self.user_bracket
        ].mean()
        duration_months = self.end_age - self.start_age

        st.markdown("#### Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total Cost", value=f"${total_cost:,.0f}")
            st.metric(label="Duration", value=f"{duration_months} months")
            st.metric(label="State", value=self.user_state)
        with col2:
            st.metric(
                label="Avg. Monthly Cost", value=f"${avg_monthly_cost:,.0f}"
            )
            st.metric(
                label="Cost Bracket",
                value=self.cost_bracket,
                help="(Based on your expectations)",
            )
            st.metric(label="Care Type", value=self.care_type)

    def display_savings(self):
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

    def display_references(self) -> None:
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

    def run(self):
        st.set_page_config(page_title="ChildCare Calculator", layout="wide")

        st.markdown(
            """
            <div class="header">

            # Childcare Calculator

            Use this tool to estimate the total cost of child care in your area.
            We use state averages from [Child Care Aware](https://www.childcareaware.org/), along with assumptions about child care duration and
                cost brackets, to provide an illustrative estimate.
                    *Always do your own research before making financial decisions*.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Load CSS
        with open(self.config.style) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

        # Load CSS

        # # Get user choice
        # with st.container():
        #     self.get_user_choice()

        with st.container():
            self.get_user_input()

        with st.container():
            self.calculate_costs()
            self.display_tuition_metrics()

        with st.container():
            self.get_daycare_duration()
            self.display_cumulative_cost()

        with st.container():
            self.display_summary_card()

        with st.container():
            self.display_savings()

        with st.container():
            st.markdown(
                """
                <div class="signature">

                Made with ❤️ by Marcio // [**Buy me a Beer 🍺**](https://buymeacoffee.com/marciooo)

                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()
        self.display_references()


if __name__ == "__main__":
    config = load_config()
    app = ChildcareCostEstimator(config)
    app.run()
