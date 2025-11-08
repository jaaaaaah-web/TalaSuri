# pages/2_Analytics_Tool.py
import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
import datetime

# --- Import your project files ---
from data_processing import load_and_clean_data, geocode_dataframe, auto_detect_columns
from analysis import run_enhanced_analysis, find_optimal_k, prepare_data_for_clustering
from ui_components import (
    display_temporal_heatmap,
    display_elbow_plot,
    display_parallel_coordinates,
    display_bubble_map,
    display_source_credibility
)

# --- App Configuration ---
st.set_page_config(
    page_title="Analytics Tool - TalaSuri",
    layout="wide"
)

# --- !!! NEW CSS TO HIDE NAVIGATION !!! ---
# This hides the page navigation links but keeps the sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)
# --- END NEW CSS ---


# --- File Storage Setup ---
UPLOAD_DIRECTORY = "user_uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# --- USER AUTHENTICATION (Needed for auth check and logout) ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- ROBUST SESSION STATE INITIALIZATION (copy from app.py) ---
default_session_state = {
    "step": "upload", "data": None, "detected_cols": {}, "prepared_data": None,
    "analysis_results": None, "optimal_k": 4, "inertias": None
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Retrieve auth status
authentication_status = st.session_state.get('authentication_status')
name = st.session_state.get('name')
username = st.session_state.get('username')


# --- !!! --- NEW LOGIC ORDER --- !!! ---

# --- 1. LOGOUT LOGIC (MOVED HERE) ---
# We must render the sidebar and logout button *before* the auth guard.
# This ensures that if the user clicks "Logout," the rerun
# command executes properly.
if authentication_status:
    st.sidebar.title(f"Welcome {name}!")
    if authenticator.logout('Logout', 'sidebar'):
        # On logout, reset session state
        for key, value in default_session_state.items():
            st.session_state[key] = value
        # Force navigation to home page by using rerun, which will trigger auth guard
        # and redirect unauthenticated users
        st.rerun()


# --- 2. AUTHENTICATION GUARD (MOVED HERE) ---
# This is the "gate" that protects your app.
if not authentication_status:
    st.error("You must be logged in to access this page.")
    st.info("Redirecting to home page...")
    # Redirect to the landing page
    st.switch_page("app.py")

# --- !!! --- END OF NEW LOGIC ORDER --- !!! ---


# --- MAIN APP (This code only runs AFTER successful login) ---
# (The old sidebar/logout logic has been removed from here)

st.title("TalaSuri: A Spatio-Temporal Fake News Detection and Localization System")
st.caption("Analyze spatiotemporal patterns in your news reports.")


# --- STEP 1: UPLOAD ---
if st.session_state.step == "upload":
    st.header("Welcome!")
    st.markdown("""
    This tool helps you analyze your news report data to find out who did the posts,
    when, and where, along with  their credibility based on the news outlet reputation.
    
    **Upload your CSV file and the system will automatically analyze it for you.**
    """)
    st.write("---")
    
    uploaded_file = st.file_uploader("Upload your News Data (CSV)", type=['csv'])

    if uploaded_file:
        # --- File Database Logic ---
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{now}_{username}_{uploaded_file.name}"
        filepath = os.path.join(UPLOAD_DIRECTORY, filename)
        
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ File saved as '{filename}'.")

        # --- Load and Process the file ---
        raw_data = load_and_clean_data(filepath)
        if not raw_data.empty:
            st.session_state.data = raw_data
            st.dataframe(st.session_state.data.head())
            st.session_state.detected_cols = auto_detect_columns(st.session_state.data.columns)
            
            if st.button("🚀 Analyze My Data", type="primary", use_container_width=True):
                # --- AUTOMATIC STEP 2: Column Mapping (Hidden from user) ---
                with st.spinner("🔍 Detecting columns and preparing data..."):
                    # Use auto-detected columns
                    loc_col = st.session_state.detected_cols['location']
                    time_col = st.session_state.detected_cols['timestamp']
                    source_col = st.session_state.detected_cols['source']
                    label_col = st.session_state.detected_cols['label']
                    
                    # Prepare data with geocoding
                    prepared_data = geocode_dataframe(
                        st.session_state.data,
                        loc_col,
                        time_col,
                        source_col,
                        label_col
                    )
                    
                    if prepared_data is not None and not prepared_data.empty:
                        st.session_state.prepared_data = prepared_data
                        
                        # --- AUTOMATIC STEP 3: Find Optimal K (Hidden from user) ---
                        st.spinner("📊 Finding optimal patterns...")
                        scaled_data, _ = prepare_data_for_clustering(prepared_data, n_components=None)
                        inertias, optimal_k = find_optimal_k(scaled_data)
                        st.session_state.inertias = inertias
                        st.session_state.optimal_k = optimal_k
                        
                        # Move directly to analysis
                        st.session_state.step = "analysis"
                        st.rerun()
                    else:
                        st.error("❌ Failed to prepare data. Please check your file format.")


# --- STEP 2: RUN ANALYSIS & SHOW RESULTS ---
if st.session_state.step == "analysis":

    # --- "GO BACK" BUTTON ---
    st.sidebar.write("---")
    if st.sidebar.button("Start New Analysis (Go Back)"):
        # Reset all session state keys, but keep user logged in
        for key, value in default_session_state.items():
            st.session_state[key] = value
        st.rerun()
    st.sidebar.write("---")
    # --- END BUTTON ---

    st.header("Analysis Results")
    
    # Use optimal K automatically (hidden from non-technical users)
    n_clusters = st.session_state.optimal_k

    if st.session_state.analysis_results is None:
        st.info(f"Click the button below to run the analysis.")
        st.write("---")

        if st.button("🔬 Run Analysis", type="primary", use_container_width=True):
            with st.spinner("Running Enhanced Analysis..."):
                st.session_state.analysis_results = run_enhanced_analysis(
                    st.session_state.prepared_data, 
                    n_clusters
                )
            st.rerun()
    else:
        # Analysis already run, allow re-running if K changes
        
            st.info(f"Analysis Completed")
        
            
    if st.session_state.analysis_results:
        
        
        if 'error' in st.session_state.analysis_results:
            st.error(f"Analysis failed: {st.session_state.analysis_results['error']}")
        else:
            st.subheader("Detailed Analysis")
            st.markdown("Click on any card below to view the analysis:")
            
            # Initialize selected view if not exists
            if 'selected_view' not in st.session_state:
                st.session_state.selected_view = None
            
            # --- Create 3 clickable cards in columns ---
            card1, card2, card3 = st.columns(3, gap="medium")
            
            # Card 1: Source Credibility
            with card1:
                with st.container(border=True):
                    st.image("assets/credibility.jpg", use_container_width=True)
                    
                    st.caption("Analyze which news sources are credible vs. non-credible")
                    if st.button("View Analysis", key="btn_credibility", use_container_width=True, type="primary"):
                        st.session_state.selected_view = "credibility"
                        st.rerun()
            
            # Card 2: Geographical Density
            with card2:
                with st.container(border=True):
                    st.image("assets/geohotspots.png", use_container_width=True)
                    
                    st.caption("Discover geographical hotspots and location patterns")
                    if st.button("View Analysis", key="btn_geo", use_container_width=True, type="primary"):
                        st.session_state.selected_view = "geo"
                        st.rerun()
            
            # Card 3: Temporal Analysis
            with card3:
                with st.container(border=True):
                    st.image("assets/time and date.jpg", use_container_width=True)
                    
                    st.caption("Identify peak activity times and temporal patterns")
                    if st.button("View Analysis", key="btn_temporal", use_container_width=True, type="primary"):
                        st.session_state.selected_view = "temporal"
                        st.rerun()
            
            st.write("---")
            
            # --- Display the selected visualization ---
            if st.session_state.selected_view == "credibility":
                
                display_source_credibility(st.session_state.analysis_results)
            
            elif st.session_state.selected_view == "geo":
                
                display_bubble_map(st.session_state.analysis_results)
            
            elif st.session_state.selected_view == "temporal":
                
                display_temporal_heatmap(st.session_state.analysis_results)
            
            else:
                # Show message when no card is selected yet
                st.info("👆 Click on any card above to view the detailed analysis.")