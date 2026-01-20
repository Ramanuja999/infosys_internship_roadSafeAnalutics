import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="Road Safety Analytics", layout="wide")
st.title("🚗 Road Safety Analytics Dashboard")
st.markdown("### Analysis of US Accidents (March 2023)")

# --- 2. LOAD DATA ---
@st.cache_data # Caches data so it doesn't reload every time you click a button
def load_data():
    # Load 50k rows for speed in the app
    df = pd.read_csv('US_Accidents_March23.csv', nrows=50000)
    
    # Cleaning
    cols_to_drop = ['End_Lat', 'End_Lng']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    df = df.dropna(subset=['Street', 'City', 'Zipcode', 'Start_Lat', 'Start_Lng'])
    df['Start_Time'] = pd.to_datetime(df['Start_Time'], errors='coerce')
    df['Hour'] = df['Start_Time'].dt.hour
    df['Weekday'] = df['Start_Time'].dt.day_name()
    return df

with st.spinner('Loading data...'):
    df = load_data()
st.success("Data loaded successfully! (50,000 Sample Rows)")

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("Filter Options")
selected_state = st.sidebar.selectbox("Select State", ['All'] + sorted(df['State'].unique().tolist()))

if selected_state != 'All':
    df_filtered = df[df['State'] == selected_state]
else:
    df_filtered = df

# --- 4. KEY METRICS ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Accidents", f"{len(df_filtered):,}")
col2.metric("Most Frequent City", df_filtered['City'].mode()[0])
col3.metric("Avg Severity (1-4)", f"{df_filtered['Severity'].mean():.2f}")

# --- 5. TABS FOR MILESTONES ---
tab1, tab2, tab3 = st.tabs(["📊 Charts (EDA)", "🗺️ Geospatial Map", "📋 Raw Data"])

# TAB 1: CHARTS
with tab1:
    st.subheader("Accident Trends")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("**Accidents by Hour of Day**")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.histplot(df_filtered['Hour'], bins=24, kde=True, color='blue', ax=ax)
        st.pyplot(fig)
        
    with col_b:
        st.write("**Accidents by Weather Condition (Top 10)**")
        fig, ax = plt.subplots(figsize=(8, 4))
        df_filtered['Weather_Condition'].value_counts().head(10).plot(kind='barh', color='orange', ax=ax)
        st.pyplot(fig)

# TAB 2: MAP
with tab2:
    st.subheader("Accident Hotspots")
    st.write("Displaying random sample of 1,000 accidents to maintain performance.")
    
    # Map centered on the average location of filtered data
    if not df_filtered.empty:
        center_lat = df_filtered['Start_Lat'].mean()
        center_lng = df_filtered['Start_Lng'].mean()
        m = folium.Map(location=[center_lat, center_lng], zoom_start=5)
        
        # Add points (limit to 1000 for speed)
        sample_map = df_filtered.sample(min(1000, len(df_filtered)))
        for i, row in sample_map.iterrows():
            folium.CircleMarker(
                location=[row['Start_Lat'], row['Start_Lng']],
                radius=3,
                color='red',
                fill=True
            ).add_to(m)
            
        st_folium(m, width=700, height=500)
    else:
        st.warning("No data available for this selection.")

# TAB 3: RAW DATA
with tab3:
    st.subheader("Dataset Preview")
    st.dataframe(df_filtered.head(100))