import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from kneed import KneeLocator

# --- Import your custom EnhancedKMeans algorithm ---
from enhanced_kmeans import EnhancedKMeans

def prepare_data_for_clustering(df, n_components=None):
    """
    Extracts features from timestamp, scales the data, and applies PCA if requested.
    """
    # Use a deep copy to ensure the original DataFrame is not modified.
    df_copy = df.copy(deep=True) 
    
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    df_copy['day_of_week'] = df_copy['timestamp'].dt.dayofweek
    
    features = ['latitude', 'longitude', 'hour', 'day_of_week']
    X = df_copy[features]

    # Step 1: Scale the data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Step 2: Apply PCA if n_components is specified and > 0
    if n_components is not None and n_components > 0:
        pca = PCA(n_components=n_components, random_state=42)
        X_processed = pca.fit_transform(X_scaled)
        
        # Add PCA component columns to the DataFrame for visualization
        for i in range(n_components):
            df_copy[f'principal_component_{i+1}'] = X_processed[:, i]
    else:
        # If no PCA, return the scaled data
        X_processed = X_scaled
        
    return X_processed, df_copy

def find_optimal_k(scaled_data, k_range=(2, 11)):
    """
    Finds the optimal k using the Elbow Method on the base scaled data (without PCA).
    """
    inertias = []
    ks = range(k_range[0], k_range[1])
    for k in ks:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(scaled_data)
        inertias.append(kmeans.inertia_)
    
    try:
        kn = KneeLocator(list(ks), inertias, curve='convex', direction='decreasing')
        optimal_k = kn.elbow if kn.elbow else 4
    except Exception:
        optimal_k = 4
        
    return inertias, optimal_k

# --- STANDARD ANALYSIS FUNCTION HAS BEEN REMOVED ---

def run_enhanced_analysis(df, n_clusters):
    """
    Runs the enhanced analysis (IF + K-Means) WITH hard-coded best parameters.
    """
    # --- HARD-CODED OPTIMAL PARAMETERS ---
    # We use the best parameters we found during our research.
    # PCA=2 gives a great 2D visualization, and 10% contamination is a robust default.
    N_COMPONENTS = 2
    CONTAMINATION = 0.1
    # --- ---------------------------- ---

    X_processed, df_with_features = prepare_data_for_clustering(df, n_components=N_COMPONENTS)

    try:
        enhanced_model = EnhancedKMeans(
            n_clusters=n_clusters,
            contamination=CONTAMINATION,
            random_state=42
        )
        labels = enhanced_model.fit_predict(X_processed)

        # Filter out the outliers (labeled as -1) for metric calculation
        inlier_mask = labels != -1
        
        if len(labels[inlier_mask]) < 2:
             return {'error': "Not enough data points remained after outlier removal to calculate performance metrics."}

        # --- ROBUST FIX for 'cluster' column ---
        if 'cluster' in df_with_features.columns:
            df_with_features = df_with_features.drop(columns=['cluster'])
        df_with_features['cluster'] = labels
        # --- END FIX ---
        
        results = {
            # We no longer need to calculate metrics, but we pass the data
            'data': df_with_features,
            'pca_components': N_COMPONENTS, # Pass n_components for visualization logic
            'X_processed': X_processed, 
            'inlier_mask': inlier_mask 
        }
        return results

    except ValueError as e:
        return {'error': str(e)}