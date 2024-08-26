import streamlit as st


def color_text(text: str, color: str) -> str:
    return f"<span style='color:{color}'>{text}</span>"


def classy_container(class_name: str = "section") -> str:
    container = st.container()
    container.markdown(f"<div class='{class_name}'>", unsafe_allow_html=True)
    return container
