import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

def load_and_clean_data(uploaded_file):
    """
    Loads data from an uploaded CSV and removes empty 'Unnamed' columns.
    """
    try:
        # Allow loading from a path (string) or an uploaded file object
        df = pd.read_csv(uploaded_file)
        df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
       
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def filter_for_fake_news(df, label_col, filter_text):
    """
    Filters the DataFrame to keep only rows matching the fake news label.
    """
    if label_col not in df.columns:
        st.warning(f"Label column '{label_col}' not found. Skipping fake news filter.")
        return df
        
    rows_before = len(df)
    df_filtered = df[df[label_col].astype(str).str.contains(filter_text, case=False, na=False)].copy()
    rows_after = len(df_filtered)
    
    st.info(f"Filtered for rows where '{label_col}' contains '{filter_text}'. Kept {rows_after} out of {rows_before} rows.")

    if rows_after == 0:
        st.error("No data remained after filtering. Please check your label column and the text you provided.")
        return None
        
    return df_filtered

def auto_detect_columns(columns):
    """
    Scans column names and automatically detects the most likely candidates
    for location, timestamp, region, label, and source.
    """
    detected_cols = {
        'location': None,
        'timestamp': None,
        'region': None,
        'label': None,
        'source': None  # NEW
    }
    
    # Define keywords for each type of column, from most to least likely
    col_keywords = {
        'location': ['location', 'loc', 'city', 'address', 'area'],
        'timestamp': ['timestamp', 'time', 'date'],
        'region': ['region', 'province'],
        'label': ['label', 'credible', 'credibility', 'type'],
        'source': ['brand', 'source', 'publisher', 'news_source'] # UPDATED to check for 'brand' first
    }

    remaining_columns = list(columns)

    for col_type, keywords in col_keywords.items():
        for keyword in keywords:
            # Find the first column that contains the keyword and hasn't been used yet
            match = next((col for col in remaining_columns if keyword in col.lower()), None)
            if match:
                detected_cols[col_type] = match
                remaining_columns.remove(match) # Ensure a column isn't used twice
                break # Move to the next column type
                
    return detected_cols

@st.cache_data
def geocode_dataframe(df_processed, loc_col, time_col, source_col, label_col, region_col=None):
    """
    Takes a DataFrame, keeps only the essential columns, and geocodes the location column.
    """
    # Step 1: Select only the essential columns the user mapped
    columns_to_keep = [loc_col, time_col, source_col, label_col] # ADDED source and label
    if region_col:
        columns_to_keep.append(region_col)
    
    df_clean = df_processed[columns_to_keep].copy()
    
    # Step 2: Drop rows with empty values in the essential columns
    rows_before = len(df_clean)
    df_clean.dropna(subset=[loc_col, time_col, source_col, label_col], inplace=True) # ADDED source and label
    rows_after = len(df_clean)
    
    if rows_after < rows_before:
        st.success(f"Preprocessing: Removed {rows_before - rows_after} empty rows (based on mapped columns).")
    
    if len(df_clean) == 0:
        st.error("No valid data remained after cleaning empty rows.")
        return None

    # Step 3: Geocoding
    st.info("Starting geocoding process... This may take a while for large datasets.")
    try:
        geolocator = Nominatim(user_agent="spatiotemporal_analysis_app", timeout=10)
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        
        unique_locations = df_clean[loc_col].unique()
        location_dict = {}
        
        progress_bar = st.progress(0, text="Geocoding locations...")
        
        for i, loc in enumerate(unique_locations):
            location_data = geocode(f"{loc}, Philippines")
            location_dict[loc] = (location_data.latitude, location_data.longitude) if location_data else (None, None)
            progress_bar.progress((i + 1) / len(unique_locations), text=f"Geocoding: {loc}")

        progress_bar.empty()

        df_clean['latitude'] = df_clean[loc_col].map(lambda loc: location_dict.get(loc, (None, None))[0])
        df_clean['longitude'] = df_clean[loc_col].map(lambda loc: location_dict.get(loc, (None, None))[1])
        
        geocoded_rows_before = len(df_clean)
        df_clean.dropna(subset=['latitude', 'longitude'], inplace=True)
        geocoded_rows_after = len(df_clean)
        
        st.info(f"Geocoding complete. Successfully mapped {geocoded_rows_after} locations. Dropped {geocoded_rows_before - geocoded_rows_after} unmappable rows.")
        
        if len(df_clean) == 0:
            st.error("Geocoding failed for all valid locations. No data remaining.")
            return None
        
        # Step 4: Final Preparation
        # This line CREATES the 'timestamp' column as a datetime object
        df_clean['timestamp'] = pd.to_datetime(df_clean[time_col], dayfirst=True, errors='coerce')
        df_clean.dropna(subset=['timestamp'], inplace=True)
        
        # Rename all columns to standard names for the app
        final_df = df_clean.rename(columns={
            loc_col: 'location',
            # --- FIX IS HERE ---
            # The line 'time_col: 'timestamp',' was removed.
            # This prevents overwriting the correct datetime column.
            # We also no longer need to keep the original time_col.
            # --- END FIX ---
            source_col: 'source',
            label_col: 'label'
        })
        
        # We can also drop the original time_col now
        if time_col in final_df.columns and time_col != 'timestamp':
            final_df = final_df.drop(columns=[time_col])
        
        if region_col and region_col in final_df.columns:
            final_df = final_df.rename(columns={region_col: 'region'})
            
        st.success(f"Final data preparation complete. Ready for analysis. Total records: {len(final_df)}.")
        return final_df

    except Exception as e:
        st.error(f"An error occurred during data preparation: {e}")
        return None