from process import analyze_statement
from visualize import render_summary
import streamlit as st
import pandas as pd

st.title("📊 Personal Finance Analyzer")

uploaded = st.file_uploader("Upload your bank statement (CSV/XLSX)", type=['csv','xlsx'])
salary_input = st.text_input("Enter salary credit dates (comma-separated YYYY-MM-DD):")

if uploaded and salary_input:
    df = pd.read_excel(uploaded) if uploaded.name.endswith('xlsx') else pd.read_csv(uploaded)
    salary_dates = [d.strip() for d in salary_input.split(',')]
    #df['Date'] = pd.to_datetime(df['Date'],format='%d/%m/%y')
    summary = analyze_statement(df, salary_dates)
    render_summary(summary)
    st.download_button("Download Summary", summary.to_csv(index=False).encode(), "summary.csv", "text/csv")
