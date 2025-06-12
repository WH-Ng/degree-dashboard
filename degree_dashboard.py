
import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("AU_all_degrees_2026.csv")

df = load_data()

st.title("🎓 Australian Degrees Explorer")
st.markdown("Search, filter and download data on 2026 degrees")

# Sidebar filters
st.sidebar.header("Filter options")

degree_name = st.sidebar.text_input("Search by Degree Name")
campus = st.sidebar.text_input("Filter by Campus")
mode = st.sidebar.multiselect("Select Mode", options=df['Mode'].dropna().unique())

# Apply filters
filtered_df = df.copy()

if degree_name:
    filtered_df = filtered_df[filtered_df['Degree Name'].str.contains(degree_name, case=False, na=False)]

if campus:
    filtered_df = filtered_df[filtered_df['Campus'].str.contains(campus, case=False, na=False)]

if mode:
    filtered_df = filtered_df[filtered_df['Mode'].isin(mode)]

# Sort option
sort_col = st.selectbox("Sort by column", options=df.columns)
ascending = st.radio("Sort order", ['Ascending', 'Descending']) == 'Ascending'
filtered_df = filtered_df.sort_values(by=sort_col, ascending=ascending)

# Display data
st.write(f"Showing {len(filtered_df)} results")
st.dataframe(filtered_df)

# Download button
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV", csv, "filtered_degrees.csv", "text/csv")
