
import streamlit as st
import pandas as pd
import os
import re
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Path to your Google service account JSON key file
SERVICE_ACCOUNT_FILE = '/Users/wayne/Personal_Project/streamlit-degree-dashboard-a41ee170648d.json' 

# Your Google Sheet ID (from the URL of your spreadsheet)
SPREADSHEET_ID = '1_6ZyxLbQT2CyUdiRV5wLbjv8f8OimORe9ErVPxIraXQ' # Replace with your sheet ID

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

try:
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    print("Google Sheets connection successful!")
except Exception as e:
    sheet = None
    print(f"Google Sheets authorization failed: {e}")

HEADER = [
    "Timestamp", "Selected Field", "Selected Degree", "Selected Campus", 
    "Selected Mode", "Selected Start Date", "Sort Column", "Ascending", "Number of Results"
]

def ensure_header(sheet):
    try:
        first_row = sheet.row_values(1)
        if first_row != HEADER:
            sheet.delete_rows(1)  # clear first row if different
            sheet.insert_row(HEADER, 1)
    except Exception as e:
        print(f"Error ensuring header row: {e}")

def log_filter_usage(log_data: dict):
    if sheet is None:
        print("Skipping logging: No Google Sheet connection.")
        return

    try:
        ensure_header(sheet)

        values = [
            log_data.get("timestamp", ""),
            log_data.get("selected_field", ""),
            log_data.get("selected_degree", ""),
            log_data.get("selected_campus", ""),
            log_data.get("selected_mode", ""),
            log_data.get("selected_start_date", ""),
            log_data.get("sort_column", ""),
            log_data.get("ascending", ""),
            str(log_data.get("num_results", ""))
        ]
        sheet.append_row(values)
    except Exception as e:
        print(f"Failed to log filter usage: {e}")

st.set_page_config(page_title="Australian Degrees Explorer", layout="wide")

field_files = {
        "AU_accounting_commerce_ecconomics_degrees_2026.csv": "Accounting, Commerce & Economics",
        "AU_agriculture_animal_veterinary-science_degrees_2026.csv": "Agriculture, Animal & Veterinary Science",
        "AU_allied-health_degrees_2026.csv": "Allied Health",
        "AU_architecture-design_degrees_2026.csv": "Architecture & Design",
        "AU_arts_humanities_social-sciences_degrees_2026.csv": "Arts, Humanities & Social Sciences",
        "AU_aviation_degrees_2026.csv": "Aviation",
        "AU_business_marketing_management_degrees_2026.csv": "Business, Marketing & Management",
        "AU_computer-science_information-technology_degrees_2026.csv": "Computer Science & IT",
        "AU_creative_media_communication_degrees_2026.csv": "Creative, Media & Communication",
        "AU_engineering_degrees_2026.csv": "Engineering",
        "AU_health_biomedical-sciences_degrees_2026.csv": "Health & Biomedical Sciences",
        "AU_law_justice_degrees_2026.csv": "Law & Justice",
        "AU_mathematics_data-science_degrees_2026.csv": "Mathematics & Data Science",
        "AU_medicine_dentistry_oral-health_degrees_2026.csv": "Medicine, Dentistry & Oral Health",
        "AU_music_degrees_2026.csv": "Music",
        "AU_nursing_midwifery_degrees_2026.csv": "Nursing & Midwifery",
        "AU_nutrition_food-science_degrees_2026.csv": "Nutrition & Food Science",
        "AU_property_construction_real-estate_degrees_2026.csv": "Property, Construction & Real Estate",
        "AU_psychology_social-work_degrees_2026.csv": "Psychology & Social Work",
        "AU_science_environment_sustainability_degrees_2026.csv": "Science, Environment & Sustainability",
        "AU_teaching_education_degrees_2026.csv": "Teaching & Education",
        "AU_tourism_sports_events_degrees_2026.csv": "Tourism, Sport & Events"
    }

CLEAN_FIELD_LIST = [
        "Accounting, Commerce & Economics",
        "Agriculture, Animal & Veterinary Science",
        "Allied Health",
        "Architecture & Design",
        "Arts, Humanities & Social Sciences",
        "Aviation",
        "Business, Marketing & Management",
        "Computer Science & IT",
        "Creative, Media & Communication",
        "Engineering",
        "Health & Biomedical Sciences",
        "Law & Justice",
        "Mathematics & Data Science",
        "Medicine, Dentistry & Oral Health",
        "Music",
        "Nursing & Midwifery",
        "Nutrition & Food Science",
        "Property, Construction & Real Estate",
        "Psychology & Social Work",
        "Science, Environment & Sustainability",
        "Teaching & Education",
        "Tourism, Sport & Events"
    ]

def remove_html_tags(text):
    if isinstance(text, str):
        # Remove all HTML tags
        clean_text = re.sub(r'<.*?>', '', text)
        return clean_text
    return text


# Load data
@st.cache_data
def load_data():
    degrees = pd.read_csv("AU_all_degrees_2026.csv")
    subjects = pd.read_csv("AU_Recommended_Stage_2_Subjects.csv")

    # Merge on 'Degree Name'
    if 'Recommended Stage 2 Subjects' not in degrees.columns:
        degrees = degrees.merge(subjects, on='Degree Name', how='left')

    degrees['Degree Name'] = degrees['Degree Name'].astype(str).str.strip()
    degrees['Mode'] = degrees['Mode'].str.strip().str.title()
    degrees['Campus'] = degrees['Campus'].astype(str).str.strip()
    degrees['Campus'] = degrees['Campus'].replace(['nan', 'NaN', ''], pd.NA)  # Set those to real NA
    degrees['Start date'] = degrees['Start date'].astype(str).str.strip()

    field_rows = []
    for file, field_name in field_files.items():
        if os.path.exists(file):
            df_field = pd.read_csv(file)
            df_field['Degree Name'] = df_field['Degree Name'].astype(str).str.strip()
            df_field['Mode'] = df_field['Mode'].str.strip().str.title()

            for _, row in df_field.iterrows():
                field_rows.append({
                    'Degree Name': row['Degree Name'],
                    'Mode': row['Mode'],
                    'Field': field_name
                })

    field_df = pd.DataFrame(field_rows).drop_duplicates()
    degrees = degrees.merge(field_df, on=['Degree Name', 'Mode'], how='left')

    # Aggregate Fields and Modes so that each degree has one row
    agg_df = degrees.groupby(['Degree Name']).agg({
        'Field': lambda x: ' ; '.join(sorted(set(x.dropna()))),
        'Mode': lambda x: ', '.join(sorted(set(x.dropna()))),
        'Campus': lambda x: ', '.join(sorted(set(x.dropna()))),
        'Start date': 'first',
        'Guaranteed ATAR score': 'first',
        'Duration': 'first',
        'Assumed knowledge': lambda x: ', '.join(sorted(set(x.dropna()))),
        'Prerequisite': lambda x: ', '.join(sorted(set(x.dropna()))),
        'Recommended Stage 2 Subjects': lambda x: ', '.join(sorted(set(x.dropna()))),
        'Degree URL': 'first',
        # Add other columns you want to keep here...
    }).reset_index()

    # Add a list version of the field column for better filtering
    agg_df['Field List'] = agg_df['Field'].apply(lambda x: [f.strip() for f in x.split(';')] if pd.notna(x) else [])

    agg_df = agg_df.fillna('')
    #agg_df['Campus'] = agg_df['Campus'].replace('nan', 'Magill, Mount Gambier, Whyalla') # Stupid nan showing up in certain degrees
    
    return agg_df

df = load_data()
    
st.title("Adelaide University Degrees Explorer")
st.markdown("Search, filter and download data on AU 2026 degrees")

# --- Filter Data ---
df['Start date'] = df['Start date'].astype(str).str.strip()

individual_fields = sorted(
    set(f.strip() for fields in df['Field'].dropna().unique() for f in fields.split(','))
)

none_option = "-- None --"

# Initialise session_state
if 'reset_triggered' not in st.session_state:
    st.session_state.reset_triggered = False

for key in ['degree_name', 'campus', 'mode', 'start_date']:
    if key not in st.session_state:
        st.session_state[key] = none_option

with st.sidebar:
    if st.button("Reset Filters"):
        for key in ['field', 'degree_name', 'campus', 'mode', 'start_date']:
            st.session_state[key] = none_option
        st.rerun()
    
    st.header("Filter Degrees")

    all_fields = sorted(CLEAN_FIELD_LIST)

    # Filters using session state

    selected_field = st.selectbox("Select Field", options=[none_option] + CLEAN_FIELD_LIST, key='field')
    
    all_campuses = df['Campus'].dropna().str.split(',').explode().str.strip().unique()
    all_campuses = sorted(all_campuses)
    selected_campus = st.selectbox("Select Campus", options=[none_option] + all_campuses, key='campus')

    mode_options = [
        none_option,
        "100% Online",
        "On Campus",
        "Both"]

    selected_mode = st.selectbox("Select Mode", options=mode_options, key='mode')
    
    selected_start_date = st.selectbox("Select Start Date", options=[none_option] + sorted(df['Start date'].dropna().unique()), key='start_date')

selected_degree = st.selectbox("Search a Degree Name", options=[none_option] + sorted(df['Degree Name'].dropna().unique()), key='degree_name')

# --- Filter Data ---
filtered_df = df.copy()
filtered_df['Guaranteed ATAR score'] = pd.to_numeric(filtered_df['Guaranteed ATAR score'], errors='coerce')

if selected_degree != none_option:
    filtered_df = filtered_df[filtered_df['Degree Name'] == selected_degree]

if selected_campus != none_option:
    filtered_df = filtered_df[
        filtered_df['Campus'].astype(str).str.split(',').apply(
            lambda campuses: selected_campus in [c.strip() for c in campuses]
        )
    ]

if selected_mode != none_option:
    if selected_mode == "Both":
        # Mode contains both '100% Online' and 'On Campus'
        filtered_df = filtered_df[
            filtered_df['Mode'].str.contains("100% Online") & filtered_df['Mode'].str.contains("On Campus")
        ]
    else:
        # Mode contains exactly the selected_mode only (no commas or others)
        filtered_df = filtered_df[
            filtered_df['Mode'].str.strip() == selected_mode
        ]

if selected_start_date != none_option:
    filtered_df = filtered_df[filtered_df['Start date'] == selected_start_date]

#if st.session_state.field != none_option:
 #   filtered_df = filtered_df[filtered_df['Field'].str.contains(st.session_state.field)]

if st.session_state.field != none_option:
    filtered_df = filtered_df[filtered_df['Field List'].apply(lambda fields: st.session_state.field in fields)]

# --- Sort Options ---
#st.markdown("##### Sort Options")
col_sort1, col_sort2 = st.columns([2, 1])
with col_sort1:
    sort_col = st.selectbox("Sort by", options=['Degree Name', 'Guaranteed ATAR score', 'Duration'])
with col_sort2:
    ascending = st.radio("Sort order", ['Ascending', 'Descending'], horizontal=True) == 'Ascending'



if filtered_df.empty:
    st.warning("No results found for the selected filters.")
else:
    filtered_df = filtered_df.sort_values(by=sort_col, ascending=ascending)

    # --- Make Degree Name clickable for display ---
    def make_clickable(name, url):
        return f'<a href="{url}" target="_blank">{name}</a>'

    display_df = filtered_df.copy()
    display_df['Degree Name'] = display_df.apply(
        lambda row: make_clickable(row['Degree Name'], row['Degree URL']), axis=1
    )
    display_df = display_df.drop(columns=['Degree URL'])

    st.markdown(f"Showing {len(display_df)} Results")
    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # --- Download ---
    with st.sidebar:
        st.markdown("---")
    
        # Your CSV export code here
        csv_export_df = filtered_df.copy()
        csv_export_df['Degree Name'] = csv_export_df['Degree Name'].apply(remove_html_tags)
        csv_export_df = csv_export_df.drop(columns=['Field List'], errors='ignore')
    
        csv = csv_export_df.to_csv(index=False).encode('utf-8')
    
        download_clicked = st.download_button("Download CSV", csv, "filtered_degrees.csv", "text/csv")
    
        if download_clicked:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "selected_field": st.session_state.get('field', '-- None --'),
                "selected_degree": st.session_state.get('degree_name', '-- None --'),
                "selected_campus": st.session_state.get('campus', '-- None --'),
                "selected_mode": st.session_state.get('mode', '-- None --'),
                "selected_start_date": st.session_state.get('start_date', '-- None --'),
                "sort_column": sort_col,
                "ascending": ascending,
                "num_results": len(filtered_df),
            }
            log_filter_usage(log_data)

with st.sidebar.expander("Feedback", expanded=False):
    st.markdown("Help us improve the dashboard!")

    feedback_rating = st.slider("How useful is this dashboard to you?", 1, 5, 3)
    feedback_text = st.text_area("Any suggestions, bugs, or ideas? (Optional)")

    if st.button("Submit Feedback"):
        from datetime import datetime

        feedback_log = {
            "timestamp": datetime.now().isoformat(),
            "rating": feedback_rating,
            "feedback": feedback_text
        }

        # Save to Google Sheet if available
        if client:
            try:
                feedback_sheet = client.open_by_key(SPREADSHEET_ID).worksheet("User Feedback")
                feedback_sheet.append_row([feedback_log["timestamp"], feedback_log["rating"], feedback_log["feedback"]])
                st.success("Thanks for your feedback!")
            except Exception as e:
                st.error("Failed to submit feedback.")
                print(f"Feedback logging error: {e}")
        else:
            st.error("Google Sheet connection not active.")
