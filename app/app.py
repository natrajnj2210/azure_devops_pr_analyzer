import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import pandas as pd
from services.azure_devops_api import fetch_pr_data


st.set_page_config(page_title="Azure DevOps PR Extractor", layout="centered")

st.title("🔍 Azure DevOps PR File Extractor (PAT Auth Only)")
st.markdown("Get all files added/modified in a Pull Request and export as CSV.")

pat = st.text_input("🔑 Enter your Personal Access Token", type="password")
org = st.text_input("🏢 Organization Name")
project = st.text_input("📁 Project Name")
repo = st.text_input("📂 Repository Name")
pr_number = st.text_input("🔢 Pull Request Number")

if st.button("Fetch & Generate CSV"):
    org, project, repo, pr_number = map(str.strip, [org, project, repo, pr_number])

    # ✅ Safe numeric conversion for PR
    try:
        pr_number = int(pr_number)
    except ValueError:
        st.error("❌ Pull Request Number must be a valid number.")
        st.stop()

    if not (pat and org and project and repo and pr_number):
        st.error("⚠️ Please fill in all fields.")
        st.stop()

    try:
        with st.spinner("Fetching PR data from Azure DevOps... ⏳"):
            df = fetch_pr_data(org, project, repo, pr_number, pat)

        if df is None or df.empty:
            st.warning("No data found for this PR.")
        else:
            st.success("✅ Data fetched successfully!")
            st.dataframe(df)

            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"PR_{pr_number}_files.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.exception(e)
