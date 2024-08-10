import streamlit as st
import yaml
import importlib
import os

# Load configuration
with open('../config/config.yaml', 'r') as config_file:
  config = yaml.safe_load(config_file)

# load cost multipliers
with open('../config/cost_multipliers.yaml', 'r') as cost_multipliers_file:
  cost_multipliers = yaml.safe_load(cost_multipliers_file)

# Load chosen CSS
css_file = config['style']
with open(f'../{css_file}', 'r') as f:
  st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Import chosen template
template_name = config['template']
template = importlib.import_module(
    f'..templates.{template_name}', package=__name__)

# Use the imported template
template.run()
