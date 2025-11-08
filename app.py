# app.py
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import base64

# --- Function to encode image ---
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# --- App Configuration ---
st.set_page_config(
    page_title="TalaSuri: A Spatio-Temporal Fake News Detection and Localization System",
    page_icon="📊",
    layout="wide"
)

# --- LOGIN MODAL DIALOG ---
@st.dialog("Account Login")
def login_modal():
    """Modal dialog for user login"""
    # Add background image to modal
    st.markdown(
        f"""
        <style>
        [data-testid="stDialog"] > div:first-child {{
            background: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)), url(data:image/jpeg;base64,{get_base64_image("assets/blb.jpg")}) !important;
            background-size: cover !important;
            background-position: center !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("Please enter your credentials to access the system.")
    
    # Render the login form inside the modal
    authenticator.login(location='main', fields={'Form name': ''})
    
    if st.session_state.authentication_status == False:
        st.error('Username/password is incorrect')
    elif st.session_state.authentication_status == None:
        st.warning('Please enter your username and password.')
    elif st.session_state.authentication_status:
        st.success(f'Welcome {st.session_state.name}!')
        st.info('Redirecting to Analytics Tool...')
        # Automatically redirect to Analytics Tool after successful login
        st.switch_page("pages/2_Analytics_Tool.py")

# --- STYLES (CSS) ---
st.markdown(
    """
    <style>
        /* --- Hide sidebar on landing page --- */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        /* --- Reduced padding in main container --- */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
        
        /* --- Reduce spacing between sections --- */
        .main h2 {
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        
        /* --- Card hover effects --- */
        [data-testid="stVerticalBlock"] [data-testid="column"] > div {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        [data-testid="stVerticalBlock"] [data-testid="column"] > div:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
        }
        
        /* --- Alternating section backgrounds --- */
        [data-testid="stVerticalBlock"]:nth-child(4) {
            background-color: #f9fafb;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
        }
        
        /* --- Footer styling - compact and centered --- */
        .footer {
            text-align: center;
            padding: 0.75rem;
            margin-top: 2rem;
            margin-bottom: 0.5rem;
            margin-left: auto;
            margin-right: auto;
            color: black;
            border-radius: 25px;
            font-weight: 500;
            font-size: 0.8rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- USER AUTHENTICATION ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- SESSION STATE ---
default_session_state = {
    "step": "upload", "data": None, "detected_cols": {}, "prepared_data": None,
    "analysis_results": None, "optimal_k": 4, "inertias": None
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

authentication_status = st.session_state.get('authentication_status')

# --- Encode background images ---
bg_image = get_base64_image("assets/blb.jpg")
login_bg_image = get_base64_image("assets/blb.jpg")

# --- PAGE LAYOUT (Two Columns) ---
col1, col2 = st.columns([1.5, 1], gap="large")

# --- COLUMN 1: Content (Left) ---
with col1:
    # Hero section - Shortened and more impactful
    st.markdown(
    """
    <h1 style='font-size: 3rem; font-weight: 800;
               -webkit-background-clip: text; -webkit-text-fill-color: blue;
               margin-bottom: 0;'>
    TalaSuri
    </h1>
    
    <p style='font-size: 1.1rem; color: #6b7280; font-weight: 600;
              margin-top: 0; margin-bottom: 0;'>
    A Spatio-Temporal Fake News Detection System
    </p>
    
    <p style='font-size: 1rem; color: #4b5563; margin-bottom: 0.1rem; line-height: 1.6;
              margin-top: 0;'>
    Uncover patterns in news reports. Discover <strong style='color: #667eea;'>who</strong> is reporting, 
    <strong style='color: #667eea;'>where</strong> it's happening, and <strong style='color: #667eea;'>when</strong>.
    </p>
    """,
    unsafe_allow_html=True
)

    st.markdown('<h2 style="color:blue;"> What You Can Discover</h2>', unsafe_allow_html=True)
    
    
    
    # --- IMPROVED CARD LAYOUT (Discover) - With background images ---
    c1, c2, c3 = st.columns(3, gap="medium")
    
    with c1:
        st.markdown(
            f"""
            <div style='background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url(data:image/jpeg;base64,{bg_image}); 
            background-size: cover; background-position: center; padding: 1.5rem; border-radius: 10px; border: 1px solid #e5e7eb; min-height: 180px;'>
                <h4 style='color: #1f2937; margin-bottom: 0.5rem;'>✅ Source Credibility</h4>
                <p style='color: #4b5563; font-size: 0.95rem;'>Identify credible vs. non-credible news sources with visual analytics.</p>
                <p style='color: #6b7280; font-size: 0.85rem;'>📊 Real-time verification</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div style='background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url(data:image/jpeg;base64,{bg_image}); 
            background-size: cover; background-position: center; padding: 1.5rem; border-radius: 10px; border: 1px solid #e5e7eb; min-height: 180px;'>
                <h4 style='color: #1f2937; margin-bottom: 0.5rem;'>📍 Geographical Hotspots</h4>
                <p style='color: #4b5563; font-size: 0.95rem;'>Interactive map of news activity locations across the Philippines.</p>
                <p style='color: #6b7280; font-size: 0.85rem;'>🗺️ Interactive mapping</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"""
            <div style='background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url(data:image/jpeg;base64,{bg_image}); 
            background-size: cover; background-position: center; padding: 1.5rem; border-radius: 10px; border: 1px solid #e5e7eb; min-height: 180px;'>
                <h4 style='color: #1f2937; margin-bottom: 0.5rem;'>⏰ Peak Activity Times</h4>
                <p style='color: #4b5563; font-size: 0.95rem;'>Discover busiest days and hours for news reporting.</p>
                <p style='color: #6b7280; font-size: 0.85rem;'>📈 Time-based insights</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown('<h2 style="color:blue;">How It Works</h2>', unsafe_allow_html=True)
    
    # --- IMPROVED CARD LAYOUT (How It Works) - With background images ---
    c4, c5, c6 = st.columns(3, gap="medium")
    with c4:
        st.markdown(
            f"""
            <div style='background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url(data:image/jpeg;base64,{bg_image}); 
            background-size: cover; background-position: center; padding: 1.5rem; border-radius: 10px; border: 1px solid #e5e7eb; min-height: 150px;'>
                <h4 style='color: #1f2937; margin-bottom: 0.5rem;'>1️⃣ Upload Data</h4>
                <p style='color: #4b5563; font-size: 0.95rem;'>Start with a CSV file containing your news data.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c5:
        st.markdown(
            f"""
            <div style='background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url(data:image/jpeg;base64,{bg_image}); 
            background-size: cover; background-position: center; padding: 1.5rem; border-radius: 10px; border: 1px solid #e5e7eb; min-height: 150px;'>
                <h4 style='color: #1f2937; margin-bottom: 0.5rem;'>2️⃣ Automatic Analysis</h4>
                <p style='color: #4b5563; font-size: 0.95rem;'>The System cleans, processes, and analyzes automatically.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c6:
        st.markdown(
            f"""
            <div style='background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url(data:image/jpeg;base64,{bg_image}); 
            background-size: cover; background-position: center; padding: 1.5rem; border-radius: 10px; border: 1px solid #e5e7eb; min-height: 150px;'>
                <h4 style='color: #1f2937; margin-bottom: 0.5rem;'>3️⃣ Get Insights</h4>
                <p style='color: #4b5563; font-size: 0.95rem;'>Explore visualizations and download reports.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# --- COLUMN 2: Login Box (Right) ---
with col2:
    # Add vertical spacing to center the login box
    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    
    # Add inline style for login box background
    st.markdown(
        f"""
        <style>
        [data-testid="column"]:last-child [data-testid="stVerticalBlock"] > div:has(div[data-testid="stVerticalBlock"]) {{
            background: linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)), url(data:image/jpeg;base64,{login_bg_image}) !important;
            background-size: cover !important;
            background-position: center !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    with st.container(border=True):
        
        if authentication_status:
            # --- Logged-In State ---
            st.markdown("### 👋 Welcome Back!")
            st.success(f"**{st.session_state.name}**")
            st.markdown("---")
            st.page_link(
                "pages/2_Analytics_Tool.py", 
                label="🚀 Go to Analytics Tool", 
                icon="📊", 
                use_container_width=True
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Logout Button ---
            if authenticator.logout('🚪 Logout', 'main'):
                # Reset session state on logout
                for key, value in default_session_state.items():
                    st.session_state[key] = value
                
                # Rerun to refresh the page and show logged-out state
                st.rerun()
        else:
            # --- Logged-Out State ---
            st.markdown("### 🔐 Access the Tool")
            st.info("Log in to start analyzing your news data")
            
            # Button to trigger login modal
            if st.button(
                "🔑 Proceed to Login", 
                type="primary",
                use_container_width=True
            ):
                login_modal()
            
            # --- How to Use the System ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("##### 📖 How to Use the System")
            st.markdown(
                """
                <div style='font-size: 0.9rem; color: #4b5563; line-height: 1.8;'>
                <strong>1.</strong> Upload your CSV file<br>
                <strong>2.</strong> Wait for automatic analysis<br>
                <strong>3.</strong> Click on cards to view results<br>
                <strong>4.</strong> Download your reports
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("Need an account? Contact your system administrator")

# --- FOOTER ---
st.markdown(
    '<div class="footer">All Rights Reserved 2025</div>', 
    unsafe_allow_html=True
)