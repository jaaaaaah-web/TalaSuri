import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- Helper Function for Color Mapping ---
def get_colors(num_colors):
    """Returns a list of distinct hex colors."""
    colors = [
        "#FF0000", "#0000FF", "#00FF00", "#FFFF00", "#FF00FF",
        "#00FFFF", "#FFA500", "#800080", "#008000", "#800000"
    ]
    return [colors[i % len(colors)] for i in range(num_colors)]

# --- Elbow Plot Function ---
def display_elbow_plot(inertias, optimal_k):
    """Displays the Elbow Method plot to help choose K."""
    st.subheader("Optimal K Determination (Elbow Method)")
    
    elbow_df = pd.DataFrame({
        'Number of Clusters (K)': range(2, len(inertias) + 2),
        'Inertia': inertias
    })
    
    chart = alt.Chart(elbow_df).mark_line(point=True).encode(
        x=alt.X('Number of Clusters (K):O', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Inertia:Q', title='Inertia'),
        tooltip=['Number of Clusters (K)', 'Inertia']
    ).properties(
        title="Elbow Method for Optimal K"
    )
    
    # Add a vertical line to mark the detected elbow
    elbow_rule = alt.Chart(pd.DataFrame({'K': [optimal_k]})).mark_rule(color='red', strokeDash=[3,3]).encode(
        x='K:O'
    )
    
    st.altair_chart(chart + elbow_rule, use_container_width=True)
    st.success(f"**Data-Driven Recommendation:** The optimal number of clusters (K) found for this dataset is **{optimal_k}**. The slider in the sidebar has been set to this value.")

# --- NEW: Source Credibility Chart ---
def display_source_credibility(analysis_results):
    """Displays a stacked bar chart of source credibility."""
    st.subheader("News Source Credibility Analysis")
    
    # Use the original data from the results, which contains 'source' and 'label'
    data = analysis_results['data'].copy()
    
    if 'source' not in data.columns or 'label' not in data.columns:
        st.warning("Could not find 'source' or 'label' columns. Please re-check your column mapping in Step 2.")
        return

    # Create a simple "credible" vs "not credible" categorization
    # This makes assumptions, you may need to adjust the keywords
    def categorize_label(label):
        label_str = str(label).lower()
        if 'not' in label_str or 'fake' in label_str or 'false' in label_str:
            return 'Not Credible'
        if 'credible' in label_str or 'real' in label_str or 'true' in label_str:
            return 'Credible'
        return 'Other/Uncategorized'

    data['Credibility'] = data['label'].apply(categorize_label)
    
    # Create the stacked bar chart
    chart = alt.Chart(data).mark_bar().encode(
        # X-axis shows the count of posts
        x=alt.X('count()', title="Number of Posts"),
        # Y-axis shows the news source/brand
        y=alt.Y('source', title="News Source / Brand", sort='-x'),
        # Color segments the bar by credibility
        color=alt.Color('Credibility', scale=alt.Scale(domain=['Credible', 'Not Credible', 'Other/Uncategorized'],
                                                    range=['#1f77b4', '#d62728', '#7f7f7f'])),
        # Tooltip for interactivity
        tooltip=['source', 'Credibility', 'count()']
    ).properties(
        title="Post Credibility by News Source"
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)
    st.caption("This chart shows the total number of posts from each source, color-coded by their credibility label.")


# --- Bubble Map ---
def display_bubble_map(analysis_results):
    """Displays an interactive map showing credibility hotspots."""
    st.subheader("Geographical Distribution of News Reports")
    data = analysis_results['data'].copy()
    
    if data.empty:
        st.warning("No data available to display.")
        return
    
    # Check if we have the necessary columns
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        st.warning("Location data (latitude/longitude) not available.")
        return
    
    if 'label' not in data.columns:
        st.warning("Credibility label column not available.")
        return
    
    # Filter out any invalid coordinates
    data = data.dropna(subset=['latitude', 'longitude', 'label'])
    
    # Classify as Fake or Credible based on label (same logic as source credibility chart)
    def categorize_label(label):
        label_str = str(label).lower()
        if 'not' in label_str or 'fake' in label_str or 'false' in label_str:
            return 'Fake News'
        if 'credible' in label_str or 'real' in label_str or 'true' in label_str:
            return 'Credible News'
        return 'Unknown'
    
    data['credibility'] = data['label'].apply(categorize_label)
    
    # Filter out Unknown categories for cleaner visualization
    data = data[data['credibility'] != 'Unknown']
    
    if data.empty:
        st.warning("No credibility data available after filtering.")
        return
    
    # --- INTERACTIVE MAP with Real Geography ---
    st.markdown("### 🗺️ Interactive Map: News Report Locations")
    
    # Add filter options
    map_filter = st.radio(
        "Select what to display on the map:",
        ["Show Both", "Fake News Only", "Credible News Only"],
        horizontal=True
    )
    
    # Aggregate data by location for cleaner display
    map_data = data.groupby(['location', 'latitude', 'longitude', 'credibility']).size().reset_index(name='count')
    
    # Filter based on selection
    if map_filter == "Fake News Only":
        map_data = map_data[map_data['credibility'] == 'Fake News']
    elif map_filter == "Credible News Only":
        map_data = map_data[map_data['credibility'] == 'Credible News']
    
    # Create separate traces for better control
    fake_data = map_data[map_data['credibility'] == 'Fake News']
    credible_data = map_data[map_data['credibility'] == 'Credible News']
    
    # Create the interactive map using Plotly with separate traces
    fig = go.Figure()
    
    # Add Credible News first (will be behind)
    if not credible_data.empty:
        fig.add_trace(go.Scattermapbox(
            lat=credible_data['latitude'],
            lon=credible_data['longitude'],
            mode='markers',
            marker=dict(
                size=credible_data['count'].apply(lambda x: min(x/2 + 10, 35)),
                color='#44bb44',
                opacity=0.8
            ),
            text=credible_data['location'],
            customdata=credible_data[['location', 'count']],
            hovertemplate='<b>%{customdata[0]}</b><br>✅ Credible News<br>Reports: %{customdata[1]}<extra></extra>',
            name='Credible News'
        ))
    
    # Add Fake News second (will be on top) with slightly smaller size to show both
    if not fake_data.empty:
        fig.add_trace(go.Scattermapbox(
            lat=fake_data['latitude'],
            lon=fake_data['longitude'],
            mode='markers',
            marker=dict(
                size=fake_data['count'].apply(lambda x: min(x/2 + 10, 35)),
                color='#ff4444',
                opacity=0.8
            ),
            text=fake_data['location'],
            customdata=fake_data[['location', 'count']],
            hovertemplate='<b>%{customdata[0]}</b><br>🔴 Fake News<br>Reports: %{customdata[1]}<extra></extra>',
            name='Fake News'
        ))
    
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=12.8797, lon=121.7740),
            zoom=5
        ),
        showlegend=True,
        legend=dict(
            title='News Type',
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(255,255,255,0.9)'
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=600,
        title='Interactive Map: Use filter above to focus on specific news types'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("💡 Use the filter above to toggle between viewing all reports, only fake news, or only credible news. Click on markers for details.")
    st.caption("💡 Zoom, pan, and click on markers to explore the data. Red markers indicate fake news hotspots requiring attention.")
    # Calculate insights
    fake_count = len(data[data['credibility'] == 'Fake News'])
    credible_count = len(data[data['credibility'] == 'Credible News'])
    total_count = len(data)
    fake_percentage = (fake_count / total_count * 100) if total_count > 0 else 0
    
    st.info(f"🔴 **Fake News Reports:** {fake_count} ({fake_percentage:.1f}%) | 🟢 **Credible Reports:** {credible_count} ({100-fake_percentage:.1f}%)")
    
    st.divider()
    
    # --- TOP LOCATIONS BAR CHART ---
    st.markdown("### 📍 Top 10 Locations by Report Count")
    
    location_counts = data.groupby(['location', 'credibility']).size().reset_index(name='count')
    top_locations = location_counts.groupby('location')['count'].sum().nlargest(10).index
    top_location_data = location_counts[location_counts['location'].isin(top_locations)]
    
    bar_chart = alt.Chart(top_location_data).mark_bar().encode(
        x=alt.X('sum(count):Q', title='Number of Reports'),
        y=alt.Y('location:N', title='Location', sort='-x'),
        color=alt.Color('credibility:N',
                       scale=alt.Scale(
                           domain=['Fake News', 'Credible News'],
                           range=['#ff4444', '#44bb44']
                       ),
                       title='News Type'
        ),
        tooltip=[
            alt.Tooltip('location:N', title='Location'),
            alt.Tooltip('credibility:N', title='Type'),
            alt.Tooltip('sum(count):Q', title='Reports')
        ]
    ).properties(
        title="Most Active Locations",
        height=400
    )
    
    st.altair_chart(bar_chart, use_container_width=True)
    
    # Get top fake news location
    fake_by_location = data[data['credibility'] == 'Fake News'].groupby('location').size().reset_index(name='count')
    if not fake_by_location.empty:
        top_fake_location = fake_by_location.loc[fake_by_location['count'].idxmax()]
        st.warning(f"⚠️ **Highest Fake News Activity:** {top_fake_location['location']} with {int(top_fake_location['count'])} fake news reports")
    
    


# --- Temporal Heatmap ---
def display_temporal_heatmap(analysis_results):
    """Displays temporal analysis with line chart (trend) and bar chart (hourly distribution)."""
    st.subheader("Temporal Pattern Analysis")
    data = analysis_results['data'][analysis_results['data']['cluster'] != -1].copy()

    if 'hour' not in data.columns or 'day_of_week' not in data.columns:
        st.warning("Temporal features not found. Cannot display temporal patterns.")
        return
    
    # Ensure we have a proper datetime column for time series
    if 'timestamp' in data.columns:
        data['date'] = pd.to_datetime(data['timestamp']).dt.date
    
    # --- 1. LINE CHART: Reports Over Time ---
    st.markdown("### 📈 News Reports Trend Over Time")
    
    if 'date' in data.columns:
        # Group by date to count reports per day
        daily_counts = data.groupby('date').size().reset_index(name='count')
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])
        
        # Filter to show only 2013-2024 date range
        daily_counts = daily_counts[
            (daily_counts['date'] >= '2013-01-01') & 
            (daily_counts['date'] <= '2024-12-31')
        ]
        
        # Sort by date to ensure proper line connection
        daily_counts = daily_counts.sort_values('date')
        
        line_chart = alt.Chart(daily_counts).mark_line(
            point=alt.OverlayMarkDef(filled=True, size=60),
            color='#1f77b4'
        ).encode(
            x=alt.X('date:T', 
                    title='Date', 
                    axis=alt.Axis(
                        format='%b %d, %Y',
                        labelAngle=-45,
                        labelOverlap=False
                    )
            ),
            y=alt.Y('count:Q', title='Number of Reports'),
            tooltip=[
                alt.Tooltip('date:T', title='Date', format='%B %d, %Y'),
                alt.Tooltip('count:Q', title='Reports')
            ]
        ).properties(
            title="Daily Report Activity (2013-2024)",
            height=300
        ).interactive()
        
        st.altair_chart(line_chart, use_container_width=True)
        
        # Calculate and display insights
        if not daily_counts.empty:
            peak_day = daily_counts.loc[daily_counts['count'].idxmax()]
            avg_daily = daily_counts['count'].mean()
            total_days = len(daily_counts)
            date_range = f"{daily_counts['date'].min().strftime('%b %d, %Y')} to {daily_counts['date'].max().strftime('%b %d, %Y')}"
            
            st.info(f"**Peak Activity:** {peak_day['date'].strftime('%B %d, %Y')} with **{int(peak_day['count'])}** reports | **Average:** {avg_daily:.1f} reports per day")
        else:
            st.warning("No data found in the 2013-2024 date range.")
    else:
        st.warning("Timestamp column not available for trend analysis.")
    
    st.divider()
    
    # --- 2. BAR CHART: Distribution by Hour of Day ---
    st.markdown("### ⏰ Activity Distribution by Hour of Day")
    
    hourly_counts = data.groupby('hour').size().reset_index(name='count')
    
    # Convert 24-hour to 12-hour format with AM/PM
    def hour_to_12hr(hour):
        if hour == 0:
            return '12 AM'
        elif hour < 12:
            return f'{hour} AM'
        elif hour == 12:
            return '12 PM'
        else:
            return f'{hour - 12} PM'
    
    hourly_counts['hour_12'] = hourly_counts['hour'].apply(hour_to_12hr)
    
    # Create proper ordering for 12-hour format
    hour_order = ['12 AM'] + [f'{i} AM' for i in range(1, 12)] + ['12 PM'] + [f'{i} PM' for i in range(1, 12)]
    
    bar_chart = alt.Chart(hourly_counts).mark_bar(color='#ff7f0e').encode(
        x=alt.X('hour_12:N', 
                title='Hour of Day', 
                axis=alt.Axis(labelAngle=-45),
                sort=hour_order
        ),
        y=alt.Y('count:Q', title='Number of Reports'),
        tooltip=[
            alt.Tooltip('hour_12:N', title='Hour'),
            alt.Tooltip('count:Q', title='Reports')
        ]
    ).properties(
        title="Reports by Hour of Day",
        height=300
    ).interactive()
    
    st.altair_chart(bar_chart, use_container_width=True)
    
    # Calculate and display insights
    peak_hour = hourly_counts.loc[hourly_counts['count'].idxmax(), 'hour']
    peak_hour_12 = hour_to_12hr(peak_hour)
    quietest_hour = hourly_counts.loc[hourly_counts['count'].idxmin(), 'hour']
    quietest_hour_12 = hour_to_12hr(quietest_hour)
    st.info(f"⏰ **Most Active:** {peak_hour_12} | **Least Active:** {quietest_hour_12}")
    
    st.divider()
    
    # --- 3. BAR CHART: Distribution by Day of Week ---
    st.markdown("### 📅 Activity Distribution by Day of Week")
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    
    data['day_name'] = data['day_of_week'].map(day_map)
    weekly_counts = data.groupby('day_name').size().reset_index(name='count')
    
    # Sort by day of week
    weekly_counts['day_order'] = weekly_counts['day_name'].map({day: i for i, day in enumerate(day_names)})
    weekly_counts = weekly_counts.sort_values('day_order')
    
    day_bar_chart = alt.Chart(weekly_counts).mark_bar(color='#2ca02c').encode(
        x=alt.X('day_name:N', title='Day of Week', sort=day_names),
        y=alt.Y('count:Q', title='Number of Reports'),
        tooltip=[
            alt.Tooltip('day_name:N', title='Day'),
            alt.Tooltip('count:Q', title='Reports')
        ]
    ).properties(
        title="Reports by Day of Week",
        height=300
    ).interactive()
    
    st.altair_chart(day_bar_chart, use_container_width=True)
    
    # Calculate and display insights
    busiest_day = weekly_counts.loc[weekly_counts['count'].idxmax(), 'day_name']
    quietest_day = weekly_counts.loc[weekly_counts['count'].idxmin(), 'day_name']
    st.info(f"📅 **Busiest Day:** {busiest_day} | **Quietest Day:** {quietest_day}")
    
    st.caption("💡 These visualizations help identify when fake news activity peaks, allowing for better monitoring and response strategies.")


# --- Parallel Coordinates Plot ---
def display_parallel_coordinates(analysis_results):
    """Displays a parallel coordinates plot to show cluster characteristics."""
    st.subheader("Cluster Characteristics (Parallel Coordinates)")
    data = analysis_results['data'][analysis_results['data']['cluster'] != -1].copy()
    
    if data.empty:
        st.warning("No clustered data available to display.")
        return
        
    num_clusters = data['cluster'].max() + 1
    cluster_names = [f'Cluster {i}' for i in range(num_clusters)]
    hex_colors = get_colors(num_clusters)
    
    data['cluster_name'] = data['cluster'].apply(lambda x: f'Cluster {int(x)}')
    
    # Features to plot
    features = ['latitude', 'longitude', 'hour', 'day_of_week']
    
    chart = alt.Chart(data).transform_window(
        index='count()'
    ).transform_fold(
        features,
        as_=['Feature', 'Value']
    ).transform_joinaggregate(
        min='min(Value)',
        max='max(Value)',
        groupby=['Feature']
    ).transform_calculate(
        # Normalize each feature to a 0-1 scale
        normalized_value='(datum.Value - datum.min) / (datum.max - datum.min)'
    ).mark_line(opacity=0.3).encode(
        x='Feature:N',
        y='normalized_value:Q',
        color=alt.Color('cluster_name:N', scale=alt.Scale(domain=cluster_names, range=hex_colors), title="Cluster"),
        detail='index:N',
        tooltip=['cluster_name', 'location']
    ).properties(
        title="Parallel Coordinates Plot of Cluster Features"
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)
    st.caption("This plot shows how each cluster is defined across all 4 original features. Each line is a data point. This helps visualize the 4D patterns the algorithm found.")