import streamlit as st


def color_text(text: str, color: str) -> str:
    return f"<span style='color:{color}'>{text}</span>"
