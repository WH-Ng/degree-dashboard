
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Australian Degrees Explorer", layout="wide")

# Load data
@st.cache_data
def load_data():
    degrees = pd.read_csv("AU_all_degrees_2026.csv")
    subjects = pd.read_csv("AU_Recommended_Stage_2_Subjects.csv")

    # Merge on 'Degree Name'
    if 'Recommended Stage 2 Subjects' not in degrees.columns:
        degrees = degrees.merge(subjects, on='Degree Name', how='left')

    return degrees

df = load_data()
    
st.title("Adelaide University Degrees Explorer")
st.markdown("Search, filter and download data on AU 2026 degrees")

# --- Filter Data ---
df['Start date'] = df['Start date'].astype(str).str.strip()
none_option = "-- None --"

# Extract individual campuses
all_campuses = df['Campus'].dropna().str.split(',').explode().str.strip().unique()
all_campuses = sorted(all_campuses)

# Initialise session_state
if 'reset_triggered' not in st.session_state:
    st.session_state.reset_triggered = False

for key in ['degree_name', 'campus', 'mode', 'start_date']:
    if key not in st.session_state:
        st.session_state[key] = none_option

with st.sidebar:
    st.header("Filter Degrees")

    # Filters using session state
    st.session_state.degree_name = st.selectbox(
        "Search a Degree Name",
        options=[none_option] + sorted(df['Degree Name'].dropna().unique()),
        index=([none_option] + sorted(df['Degree Name'].dropna().unique())).index(st.session_state.degree_name)
    )

    st.session_state.campus = st.selectbox(
        "Select Campus",
        options=[none_option] + all_campuses,
        index=([none_option] + all_campuses).index(st.session_state.campus)
    )

    st.session_state.mode = st.selectbox(
        "Select Mode",
        options=[none_option] + sorted(df['Mode'].dropna().unique()),
        index=([none_option] + sorted(df['Mode'].dropna().unique())).index(st.session_state.mode)
    )

    st.session_state.start_date = st.selectbox(
        "Select Start Date",
        options=[none_option] + sorted(df['Start date'].dropna().unique()),
        index=([none_option] + sorted(df['Start date'].dropna().unique())).index(st.session_state.start_date)
    )

    # Reset button
    if st.button("Reset Filters"):
        for key in ['degree_name', 'campus', 'mode', 'start_date']:
            st.session_state[key] = none_option
        st.rerun()

# --- Filter Data ---
filtered_df = df.copy()

if st.session_state.degree_name != none_option:
    filtered_df = filtered_df[filtered_df['Degree Name'] == st.session_state.degree_name]

if st.session_state.campus != none_option:
    filtered_df = filtered_df[
        filtered_df['Campus']
        .astype(str)
        .str.split(',')
        .apply(lambda campuses: st.session_state.campus in [c.strip() for c in campuses])
    ]

if st.session_state.mode != none_option:
    filtered_df = filtered_df[filtered_df['Mode'] == st.session_state.mode]

if st.session_state.start_date != none_option:
    filtered_df = filtered_df[filtered_df['Start date'] == st.session_state.start_date]

# --- Sort Options ---
st.markdown("##### Sort Options")
col_sort1, col_sort2 = st.columns([2, 1])
with col_sort1:
    sort_col = st.selectbox("Sort by", options=[col for col in df.columns if col != 'Degree URL'])
with col_sort2:
    ascending = st.radio("Sort order", ['Ascending', 'Descending'], horizontal=True) == 'Ascending'

filtered_df = filtered_df.sort_values(by=sort_col, ascending=ascending)

# --- Make Degree Name clickable ---
def make_clickable(name, url):
    return f'<a href="{url}" target="_blank">{name}</a>'

filtered_df['Degree Name'] = filtered_df.apply(
    lambda row: make_clickable(row['Degree Name'], row['Degree URL']), axis=1
)

# --- Remove URL column from display ---
display_df = filtered_df.drop(columns=['Degree URL'])

# --- Display Table ---
st.markdown(f"Showing {len(display_df)} Results")
st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

# --- Download ---
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV", csv, "filtered_degrees.csv", "text/csv")
