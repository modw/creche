import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def run(style_path: str):
  # Set page config
  st.set_page_config(page_title="Child Care Cost Estimator", layout="wide")

  # Read CSS file
  with open(style_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

  # Title and introduction
  st.title("📊 Child Care Cost Estimator")
  st.write(
      "Plan your child care expenses with our interactive dashboard. Estimate costs, explore different scenarios, and make informed decisions about your family's financial future."
  )

  # Sidebar for inputs
  st.sidebar.header("📝 Input Parameters")

  # Household Income
  household_income = st.sidebar.number_input(
      "Annual Household Income ($)", min_value=0, value=50000, step=5000)

  # Start Age
  st.sidebar.subheader("Age at start of care:")
  col1, col2 = st.sidebar.columns(2)
  start_age_years = col1.number_input(
      "years", min_value=0, max_value=5, value=0, step=1)

  start_age_months = col2.number_input(
      "months", min_value=0, max_value=11, value=6, step=1)

  start_age = start_age_years * 12 + start_age_months

  # End Age
  st.sidebar.subheader("Age at end of care:")
  col1, col2 = st.sidebar.columns(2)

  end_age_years = col1.number_input(
      "years", min_value=0, max_value=8, value=6, step=1)

  end_age_months = col2.number_input(
      "months", min_value=0, max_value=11, value=0, step=1)

  end_age = end_age_years * 12 + end_age_months

  # Location-based costs
  location = st.sidebar.selectbox(
      "Select Your Location", ["Urban", "Suburban", "Rural"])
  price_bracket = st.sidebar.selectbox(
      "Child Care Price Bracket", options=["Budget", "Mid-range", "Premium"])
  childcare_type = st.sidebar.selectbox(
      "Child Care Type", [
          "Center-based", "Family Care (Small Group)",
          "Family Care (Large Group)"
      ])

  # Define cost multipliers based on location and price bracket
  cost_multipliers = {
      "Urban": {
          "Budget": 1.0,
          "Mid-range": 1.5,
          "Premium": 2.0
      },
      "Suburban": {
          "Budget": 0.8,
          "Mid-range": 1.2,
          "Premium": 1.6
      },
      "Rural": {
          "Budget": 0.6,
          "Mid-range": 0.9,
          "Premium": 1.2
      }
  }

  # Base annual cost (adjust as needed)
  base_annual_cost = 10000
  annual_cost = base_annual_cost * cost_multipliers[location][price_bracket]

  # Government Programs
  gov_program = st.sidebar.checkbox("Apply Government Subsidies")
  subsidy_percentage = 0.2 if gov_program else 0

  # Pre-tax Savings Account
  use_pretax = st.sidebar.checkbox(
      "Use Pre-tax Savings Account (e.g., FSA, HSA)")
  pretax_contribution = st.sidebar.number_input(
      "Annual Pre-tax Contribution ($)",
      min_value=0,
      max_value=5000,
      value=2500,
      step=100) if use_pretax else 0

  # Multiple Children
  num_children = st.sidebar.number_input(
      "Number of Children", min_value=1, max_value=5, value=1, step=1)

  # Calculate costs
  def calculate_costs(
      years, annual_cost, subsidy_percentage, pretax_contribution):
    monthly_cost = (
        annual_cost * (1 - subsidy_percentage) - pretax_contribution) / 12
    costs = [monthly_cost] * (years * 12)
    cumulative_costs = [sum(costs[:i + 1]) for i in range(len(costs))]
    return costs, cumulative_costs

  years = end_age - start_age
  monthly_costs, cumulative_costs = calculate_costs(
      years, annual_cost, subsidy_percentage, pretax_contribution)

  # Create DataFrames for plotting
  df_monthly = pd.DataFrame(
      {
          'Month': range(1,
                         len(monthly_costs) + 1),
          'Monthly Cost': monthly_costs,
          'Cumulative Cost': cumulative_costs
      })

  # Visualizations
  st.header("📈 Cost Visualization")

  # Monthly Contributions
  fig_monthly = px.line(
      df_monthly,
      x='Month',
      y='Monthly Cost',
      title='Monthly Child Care Costs')
  fig_monthly.update_layout(yaxis_title='Cost ($)', xaxis_title='Month')
  st.plotly_chart(fig_monthly, use_container_width=True)

  # Cumulative Costs
  fig_cumulative = px.line(
      df_monthly,
      x='Month',
      y='Cumulative Cost',
      title='Cumulative Child Care Costs')
  fig_cumulative.update_layout(
      yaxis_title='Total Cost ($)', xaxis_title='Month')
  st.plotly_chart(fig_cumulative, use_container_width=True)

  # Comparative Chart
  st.subheader("💹 Cost Comparison Across Price Brackets")
  price_brackets = ["Budget", "Mid-range", "Premium"]
  comparative_costs = [
      calculate_costs(
          years, base_annual_cost * cost_multipliers[location][pb],
          subsidy_percentage, pretax_contribution)[1][-1]
      for pb in price_brackets
  ]

  fig_comparison = go.Figure(
      data=[go.Bar(name='Total Cost', x=price_brackets, y=comparative_costs)])
  fig_comparison.update_layout(
      title='Total Cost by Price Bracket', yaxis_title='Total Cost ($)')
  st.plotly_chart(fig_comparison, use_container_width=True)

  # Summary
  st.header("💡 Summary")
  total_cost = cumulative_costs[-1] * num_children
  st.write(
      f"Based on your inputs, the estimated total cost of child care until public school age for {num_children} child(ren) is: **${total_cost:,.2f}**"
  )

  if gov_program:
    savings = annual_cost * subsidy_percentage * years * num_children
    st.write(
        f"You save approximately **${savings:,.2f}** through government subsidies."
    )

  if use_pretax:
    tax_savings = pretax_contribution * 0.22 * years * num_children  # Assuming 22% tax bracket
    st.write(
        f"By using a pre-tax savings account, you save approximately **${tax_savings:,.2f}** in taxes."
    )

    st.write(
        f"Your monthly child care cost is estimated at: **${monthly_costs[0] * num_children:,.2f}**"
    )

  # Recommendations
  st.header("🎯 Recommendations")
  income_percentage = (
      monthly_costs[0] * 12 * num_children) / household_income * 100
  st.write(
      f"Your annual child care costs represent approximately **{income_percentage:.1f}%** of your household income."
  )

  if income_percentage > 10:
    st.warning(
        "Your child care costs exceed 10% of your household income. Consider exploring additional financial assistance options or more affordable care alternatives."
    )
  else:
    st.success(
        "Your child care costs are within a manageable range based on your household income."
    )

    st.info(
        "Remember to regularly review and adjust your child care budget as your circumstances change. Consider setting aside additional savings for unexpected expenses or future educational costs."
    )

  # Additional Resources
  st.header("📚 Additional Resources")
  st.write("Here are some helpful resources for managing child care costs:")
  st.markdown(
      """
    - [State Averages: Child Care Aware of America](https://www.childcareaware.org/)
    - [National Database of Child Care Financial Assistance Programs](https://childcareta.acf.hhs.gov/consumer-education)
    - [Tax Credits for Child Care Expenses](https://www.irs.gov/credits-deductions/individuals/child-and-dependent-care-credit)
    """)

  # Disclaimer
  st.caption(
      "Disclaimer: This tool provides estimates based on average costs and simplified calculations. Actual costs may vary. Always consult with a financial advisor for personalized advice."
  )


if __name__ == "__main__":
  run()
