import streamlit as st
import matplotlib.pyplot as plt

def render_summary(summary_df):
    st.dataframe(summary_df)

    # Spending ratio trend
    summary_df['Period'] = summary_df['Cycle'].str.split('→').str[0]
    summary_df['Spending'] = summary_df['Narration'].str.extract(r'Spending Ratio (\d+\.\d+)').astype(float)

    plt.figure(figsize=(8,4))
    plt.plot(summary_df['Period'], summary_df['Spending'], marker='o')
    plt.xticks(rotation=45)
    plt.ylabel('Spending Ratio (%)')
    plt.title('Monthly Spending Trend')
    st.pyplot(plt)
