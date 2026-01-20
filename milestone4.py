import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import zipfile

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Road Safety Analytics Dashboard",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Road Safety Analytics: US Accidents")
st.markdown("### Milestone 4: Interactive Dashboard")
st.markdown("Interact with the dataset to analyze accident trends by location, time, and conditions.")

# --- 2. LOAD DATA (OPTIMIZED) ---
@st.cache_data
def load_data():
    try:
        # Load only necessary columns to save memory
        cols_to_use = [
            'Severity', 'Start_Time', 'Start_Lat', 'Start_Lng', 
            'City', 'State', 'Weather_Condition'
        ]

        # Read directly from ZIP file
        with zipfile.ZipFile("US_Accidents_March23.zip", "r") as z:
            filename = "US_Accidents_March23.csv"
            with z.open(filename) as f:
                # Load 500,000 rows (Safe limit for laptops)
                df = pd.read_csv(f, usecols=cols_to_use, nrows=500000)

    except FileNotFoundError:
        st.error("⚠️ File 'US_Accidents_March23.zip' not found! Make sure it is in the same folder.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

    # Optimize Memory (Convert text to categories)
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype('category')

    # Drop missing location data
    df = df.dropna(subset=['City', 'Start_Lat', 'Start_Lng'])
    
    # Feature Engineering
    df['Start_Time'] = pd.to_datetime(df['Start_Time'], errors='coerce')
    df['Hour'] = df['Start_Time'].dt.hour
    df['Date'] = df['Start_Time'].dt.date
    df['Weekday'] = df['Start_Time'].dt.day_name().astype('category')
    
    return df

with st.spinner('Loading 500,000 records... please wait...'):
    df = load_data()

# --- 3. SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Options")

# State Filter
state_list = sorted(df['State'].unique())
selected_state = st.sidebar.selectbox("Select State", ["All"] + state_list)

# City Filter (Dynamic)
if selected_state != "All":
    city_list = sorted(df[df['State'] == selected_state]['City'].unique())
    selected_city = st.sidebar.multiselect("Select City", city_list)
else:
    selected_city = []

# Time Filter
min_hour, max_hour = st.sidebar.slider("Select Time of Day (24H)", 0, 23, (0, 23))

# Weather Filter
if 'Weather_Condition' in df.columns:
    weather_options = df['Weather_Condition'].dropna().unique().tolist()
    selected_weather = st.sidebar.multiselect("Weather Condition", options=weather_options)
else:
    selected_weather = []

# --- 4. APPLY FILTERS ---
if selected_state != "All":
    df_filtered = df[df['State'] == selected_state]
else:
    df_filtered = df.copy()

if selected_city:
    df_filtered = df_filtered[df_filtered['City'].isin(selected_city)]

df_filtered = df_filtered[(df_filtered['Hour'] >= min_hour) & (df_filtered['Hour'] <= max_hour)]

if selected_weather:
    df_filtered = df_filtered[df_filtered['Weather_Condition'].isin(selected_weather)]

# --- 5. KEY METRICS ---
st.divider()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Accidents", f"{len(df_filtered):,}")

if not df_filtered.empty:
    col2.metric("Most Frequent City", df_filtered['City'].mode()[0])
    col3.metric("Avg Severity", f"{df_filtered['Severity'].mean():.2f}")
    if 'Weather_Condition' in df_filtered.columns and not df_filtered['Weather_Condition'].mode().empty:
         col4.metric("Top Weather", df_filtered['Weather_Condition'].mode()[0])
else:
    st.warning("No data matches your filters.")
    st.stop()

# --- 6. VISUALIZATION TABS ---
tab1, tab2, tab3 = st.tabs(["🗺️ Interactive Map", "📊 Analysis Charts", "📂 Raw Data"])

# TAB 1: MAP
with tab1:
    st.subheader("Accident Locations")
    if not df_filtered.empty:
        # Center map
        center_lat = df_filtered['Start_Lat'].mean()
        center_lng = df_filtered['Start_Lng'].mean()
        m = folium.Map(location=[center_lat, center_lng], zoom_start=6)
        
        # Sample 1000 points for speed
        marker_data = df_filtered.sample(min(1000, len(df_filtered)))
        marker_cluster = MarkerCluster().add_to(m)
        
        for idx, row in marker_data.iterrows():
            color = "red" if row['Severity'] >= 3 else "blue"
            folium.Marker(
                location=[row['Start_Lat'], row['Start_Lng']],
                popup=f"{row['City']} (Sev: {row['Severity']})",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(marker_cluster)
            
        st_folium(m, width=1200, height=500)

# TAB 2: CHARTS (FIXED FOR MILESTONE 4)
with tab2:
    st.subheader("Data Insights")
    
    if not df_filtered.empty:
        col_a, col_b = st.columns(2)
        
        # Chart 1: Hourly Trends
        with col_a:
            st.markdown("**Accidents by Hour**")
            plt.clf() # Clear memory
            fig1 = plt.figure(figsize=(8, 4))
            sns.histplot(df_filtered['Hour'], bins=24, kde=True, color='teal')
            plt.xlabel("Hour (0-23)")
            plt.xlim(0, 23)
            st.pyplot(fig1, use_container_width=True)
            
        # Chart 2: Severity
        with col_b:
            st.markdown("**Severity Distribution**")
            plt.clf() # Clear memory
            fig2 = plt.figure(figsize=(8, 4))
            sns.countplot(x='Severity', data=df_filtered, palette='viridis')
            plt.xlabel("Severity Level (1-4)")
            st.pyplot(fig2, use_container_width=True)
    else:
        st.info("No data to visualize.")

# TAB 3: DATA
with tab3:
    st.subheader("Dataset Preview")
    st.dataframe(df_filtered.head(100))