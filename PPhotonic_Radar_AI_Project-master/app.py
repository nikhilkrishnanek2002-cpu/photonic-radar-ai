"""AI Cognitive Photonic Radar - Advanced Defense System"""

import os
import time

import numpy as np
import pandas as pd
import cv2
import torch
import matplotlib
import matplotlib.pyplot as plt
import streamlit as st
import plotly.graph_objects as go

matplotlib.use('Agg')

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from src.config import get_config
from src.logger import init_logging, log_event, read_logs
from src.startup_checks import run_startup_checks
# Cache the feature extraction and detection
@st.cache_data(show_spinner=False, ttl=10) # Cache for 10 seconds max
def cached_get_all_features(signal, fs=4096, rd_map=None):
    from src.feature_extractor import get_all_features
    return get_all_features(signal, fs, rd_map)

@st.cache_data(show_spinner=False, ttl=10)
def cached_detect_targets(signal, fs=4096, n_range=128, n_doppler=128, method='ca', **kwargs):
    from src.detection import detect_targets_from_raw
    return detect_targets_from_raw(signal, fs, n_range, n_doppler, method, **kwargs)

# Direct imports retained for typing but functions redirected
from src.feature_extractor import get_all_features as _uncached_features
from src.detection import detect_targets_from_raw as _uncached_detect
from src.model_pytorch import build_pytorch_model
from src.auth import authenticate
from src.security_utils import safe_path
from src.signal_generator import generate_radar_signal
from src.rtl_sdr_receiver import RTLRadar
from src.tracker import MultiTargetTracker
from src.cognitive_controller import CognitiveRadarController
from src.ew_defense import EWDefenseController
from src.db import init_db, ensure_admin_exists
from src.stream_bus import get_producer
from src.xai_pytorch import grad_cam_pytorch
from src.cognitive_logic import adaptive_threshold
from src.ai_hardening import ConfidenceEstimator, OutOfDistributionDetector
from src.tamper_detection import TamperDetector, TamperSeverity

# ===============================
# ENVIRONMENT SAFETY
# ===============================
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Initialize config, structured logging and startup checks
cfg = get_config()
init_logging(cfg)
_startup = run_startup_checks()

cfg = get_config()
init_logging(cfg)
_startup = run_startup_checks()

# ===============================
# STREAMLIT CONFIG (FIRST CALL)
# ===============================
st.set_page_config(page_title="PHOENIX-RADAR: Cognitive Photonic Radar with AI", layout="wide")

# Simple UI mode: set True for a very minimal interface
# Simple UI mode: set True for a very minimal interface
SIMPLE_UI = False

# Initialize perf_mode in session state if not present (defaults to True)
if "perf_mode" not in st.session_state:
    st.session_state.perf_mode = False # Default to 3D

# Global perf_mode variable (Correctly Initialized)
perf_mode = st.session_state.perf_mode


if SIMPLE_UI:
    st.title("Photonic Radar — Simple UI")
    st.write("Minimal interface for quick inspection and demo.")
    
    # PERFORMANCE MODE (Global for simple UI too)
    # Sidebar control for perf_mode (will be rendered in sidebar but valid here)
    perf_mode_check = st.sidebar.checkbox("🚀 High Performance Mode", value=st.session_state.perf_mode, help="Disables 3D plots and heavy effects for speed.", key="perf_mode_global")
    st.session_state.perf_mode = perf_mode_check
    perf_mode = perf_mode_check

    # Visualization controls
    colormap_rd = st.selectbox("RD colormap", ['Viridis', 'Cividis', 'Plasma', 'Magma', 'Jet'], index=0)
    colormap_sp = st.selectbox("Spectrogram colormap", ['Cividis', 'Viridis', 'Plasma', 'Magma', 'Jet'], index=0)
    x_min, x_max = st.slider("X axis range", 0, 127, (0, 127))
    y_min, y_max = st.slider("Y axis range", 0, 127, (0, 127))
    z_min, z_max = st.slider("Intensity (z) range", 0.0, 1.0, (0.0, 1.0), step=0.01)

    c1, c2 = st.columns(2)
    with c1:
        st.header("RD Map")
        rd_map_sample = np.zeros((128, 128))
        try:
            fig_rd = go.Figure(data=go.Heatmap(z=rd_map_sample, colorscale=colormap_rd, zmin=z_min, zmax=z_max))
            fig_rd.update_layout(title='RD Map (Heatmap)', xaxis_title='Range bins', yaxis_title='Doppler bins', coloraxis_showscale=True)
            fig_rd.update_xaxes(range=[x_min, x_max])
            fig_rd.update_yaxes(range=[y_min, y_max])
            st.plotly_chart(fig_rd, width='stretch')
        except Exception:
            st.image(rd_map_sample, caption="RD Map (placeholder)")
        st.button("Refresh RD Map")
    with c2:
        st.header("Spectrogram")
        spec_sample = np.zeros((128, 128))
        try:
            fig_sp = go.Figure(data=go.Heatmap(z=spec_sample, colorscale=colormap_sp, zmin=z_min, zmax=z_max))
            fig_sp.update_layout(title='Spectrogram (Heatmap)', xaxis_title='Time', yaxis_title='Frequency', coloraxis_showscale=True)
            fig_sp.update_xaxes(range=[x_min, x_max])
            fig_sp.update_yaxes(range=[y_min, y_max])
            st.plotly_chart(fig_sp, width='stretch')
        except Exception:
            st.image(spec_sample, caption="Spectrogram (placeholder)")
        st.button("Refresh Spectrogram")

    st.write("---")
    show_3d = st.checkbox("Show 3D surface (RD Map)")
    if st.button("Run Detection"):
        st.info("Running detection (simplified)...")
        try:
            rd = np.random.rand(64, 64)
            spec = np.random.rand(64, 64)
            # clearer 2D results with colorbar and labels
            fig_rd_res = go.Figure(data=go.Heatmap(z=rd, colorscale=colormap_rd, zmin=z_min, zmax=z_max))
            fig_rd_res.update_layout(title='RD Map (Result)', xaxis_title='Range bins', yaxis_title='Doppler bins')
            # clip ranges to actual data size
            x_max_clipped = max(0, min(x_max, rd.shape[1]-1))
            x_min_clipped = max(0, min(x_min, x_max_clipped))
            y_max_clipped = max(0, min(y_max, rd.shape[0]-1))
            y_min_clipped = max(0, min(y_min, y_max_clipped))
            fig_rd_res.update_xaxes(range=[x_min_clipped, x_max_clipped])
            fig_rd_res.update_yaxes(range=[y_min_clipped, y_max_clipped])
            st.plotly_chart(fig_rd_res, width='stretch')

            fig_sp_res = go.Figure(data=go.Heatmap(z=spec, colorscale=colormap_sp, zmin=z_min, zmax=z_max))
            fig_sp_res.update_layout(title='Spectrogram (Result)', xaxis_title='Time', yaxis_title='Frequency')
            x_max_clipped = max(0, min(x_max, spec.shape[1]-1))
            x_min_clipped = max(0, min(x_min, x_max_clipped))
            y_max_clipped = max(0, min(y_max, spec.shape[0]-1))
            y_min_clipped = max(0, min(y_min, y_max_clipped))
            fig_sp_res.update_xaxes(range=[x_min_clipped, x_max_clipped])
            fig_sp_res.update_yaxes(range=[y_min_clipped, y_max_clipped])
            st.plotly_chart(fig_sp_res, width='stretch')

            if show_3d:
                # build a 3D surface for RD map
                x = np.arange(rd.shape[1])
                y = np.arange(rd.shape[0])
                fig_3d = go.Figure(data=[go.Surface(z=rd, x=x, y=y, colorscale=colormap_rd)])
                fig_3d.update_layout(title='RD Map 3D Surface', scene=dict(xaxis_title='Range', yaxis_title='Doppler', zaxis_title='Intensity'))
                st.plotly_chart(fig_3d, width='stretch')

            st.success("Detection complete")
        except Exception as e:
            st.error(f"Detection error: {e}")

    st.stop()

# ===============================
# CUSTOM CSS: PROFESSIONAL COMMAND CENTER
# ===============================
st.markdown("""
<style>
    /* =========================================
       CYBERPUNK ORBITAL COMMAND THEME
       ========================================= */
       
    /* 1. Global Reset & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;600;700&family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
    
    :root {
        --neon-cyan: #00f3ff;
        --neon-purple: #bc13fe;
        --neon-green: #0aff68;
        --bg-deep: #020408;
        --bg-panel: rgba(10, 15, 30, 0.75);
        --grid-color: rgba(0, 243, 255, 0.1);
        --glass-border: 1px solid rgba(0, 243, 255, 0.3);
    }

    html, body, [class*="css"] {
        font-family: 'Rajdhani', sans-serif;
    }

    /* Main Container */
    .main {
        background: linear-gradient(135deg, #05070a 0%, #0a1428 50%, #05070a 100%);
        color: #00f0ff;
        font-family: 'Segoe UI', 'Roboto', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 2. Main App Background & Grid Overlay */
    .stApp {
        background-color: var(--bg-deep);
        background-image: 
            linear-gradient(var(--grid-color) 1px, transparent 1px),
            linear-gradient(90deg, var(--grid-color) 1px, transparent 1px),
            radial-gradient(circle at 50% 50%, rgba(20, 30, 60, 0) 0%, #020408 100%);
        background-size: 40px 40px, 40px 40px, 100% 100%;
        background-attachment: fixed;
    }

    /* 3. Typography & Headers */
    h1, h2, h3 {
        font-family: 'Orbitron', 'sans-serif';
        text-transform: uppercase;
        letter-spacing: 2px;
        color: var(--neon-cyan) !important;
        text-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
    }
    
    h1 { font-size: 3.5rem !important; margin-bottom: 0.5rem !important; }
        margin-bottom: 1rem !important;
    }
    
    h2 { font-size: 2rem !important; border-left: 5px solid var(--neon-purple); padding-left: 15px; }

    p, span, div, label {
        color: #e0e6ed;
        letter-spacing: 0.5px;
    }
    
    /* Monospace for data */
    .stCode, .stMetric, .metric-value {
        font-family: 'Share Tech Mono', monospace !important;
    }

    /* 4. Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(5, 10, 20, 0.95);
        border-right: 2px solid var(--neon-cyan);
        box-shadow: 10px 0 30px rgba(0, 0, 0, 0.5);
    }
    
    .stSidebar [data-testid="stSidebarUserContent"] {
        padding-top: 2rem;
    }

    /* 5. Glassmorphism Panels */
    .stMetric, .stInfo, .stSuccess, .stWarning, .stError, div[data-testid="stExpander"] {
        background: var(--bg-panel);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: var(--glass-border);
        border-radius: 4px; /* Angled corners aesthetic */
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
        border-color: var(--neon-cyan);
    }

    /* 6. Neon Buttons */
    .stButton > button {
        background: transparent;
        color: var(--neon-cyan);
        border: 2px solid var(--neon-cyan);
        border-radius: 2px;
        font-family: 'Orbitron', sans-serif;
        text-transform: uppercase;
        font-weight: 700;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        background: var(--neon-cyan);
        color: #000;
        box-shadow: 0 0 30px var(--neon-cyan);
        transform: scale(1.02);
    }
    
    .stButton>button:active {
        transform: translateY(-1px) scale(0.98);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        border-bottom: 2px solid rgba(0, 240, 255, 0.2);
        background: rgba(10, 20, 40, 0.3);
        padding: 10px 20px;
        border-radius: 12px 12px 0 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: 1px solid rgba(0, 240, 255, 0.3);
        padding: 12px 24px;
        border-radius: 8px;
        color: #a0b4ff;
        transition: all 0.3s ease;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(0, 240, 255, 0.1);
        border-color: #00f0ff;
        color: #00f0ff;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.3) 0%, rgba(0, 102, 255, 0.2) 100%) !important;
        border: 1.5px solid #00f0ff !important;
        color: #fff !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
    }

    /* 7. Input Fields */
    input, select, textarea {
        background-color: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid #334e68 !important;
        color: var(--neon-cyan) !important;
        font-family: 'Share Tech Mono', monospace !important;
    }
    
    input:focus {
        border-color: var(--neon-cyan) !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.3) !important;
    }

    }

    /* Checkboxes and Radio */
    .stCheckbox>label>div {
        background-color: rgba(20, 30, 60, 0.5) !important;
        border: 1px solid #00f0ff !important;
        border-radius: 4px !important;
    }
    
    .stRadio>label>div {
        border: 1px solid #00f0ff !important;
        border-radius: 50% !important;
    }

    /* Columns */
    .stColumn {
        padding: 20px;
        background: linear-gradient(135deg, rgba(10, 25, 47, 0.3) 0%, rgba(15, 35, 65, 0.2) 100%);
        border-radius: 12px;
        border: 1px solid rgba(0, 240, 255, 0.15);
        transition: all 0.3s ease;
    }
    
    .stColumn:hover {
        border-color: rgba(0, 240, 255, 0.3);
        background: linear-gradient(135deg, rgba(10, 25, 47, 0.5) 0%, rgba(15, 35, 65, 0.3) 100%);
    }

    /* Expandable Containers */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(0, 102, 255, 0.2) 0%, rgba(0, 50, 150, 0.1) 100%);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 8px;
        padding: 12px 16px !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #00f0ff;
        background: linear-gradient(135deg, rgba(0, 102, 255, 0.3) 0%, rgba(0, 50, 150, 0.2) 100%);
    }

    /* Metric Values */
    [data-testid="metric"] .metric-value {
        color: #00ff88 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="metric"] .metric-label {
        color: #a0b4ff !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Status Indicators */
    .status-active {
        color: #00ff88 !important;
        text-shadow: 0 0 10px #00ff88;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffaa00 !important;
        text-shadow: 0 0 10px #ffaa00;
        font-weight: bold;
    }
    
    .status-error {
        color: #ff4444 !important;
        text-shadow: 0 0 10px #ff4444;
        font-weight: bold;
    }

    /* Info/Alert Boxes */
    .stInfo, .stSuccess, .stWarning, .stError {
        border-radius: 12px !important;
        padding: 20px !important;
        border-left: 4px solid !important;
    }
    
    .stInfo {
        background: rgba(0, 102, 255, 0.15) !important;
        border-left-color: #0066ff !important;
    }
    
    .stSuccess {
        background: rgba(0, 255, 136, 0.15) !important;
        border-left-color: #00ff88 !important;
    }
    
    .stWarning {
        background: rgba(255, 170, 0, 0.15) !important;
        border-left-color: #ffaa00 !important;
    }
    
    .stError {
        background: rgba(255, 68, 68, 0.15) !important;
        border-left-color: #ff4444 !important;
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(10, 20, 40, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00f0ff, #0066ff);
        border-radius: 6px;
        border: 2px solid rgba(10, 20, 40, 0.5);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #33ffff, #0088ff);
    }

</style>
""", unsafe_allow_html=True)

# Conditional CSS for heavy animations
if not perf_mode:
    st.markdown("""
    <style>
    /* 8. Threat Monitor Animation */
    @keyframes scanline {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100vh); }
    }
    
    .scan-overlay {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: linear-gradient(to bottom, transparent, rgba(0, 243, 255, 0.1), transparent);
        pointer-events: none;
        animation: scanline 4s linear infinite;
        z-index: 9999;
        opacity: 0.3;
    }
    </style>
    <!-- Scanning Line Overlay -->
    <div class="scan-overlay"></div>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    /* Radar-like scanning animation for aesthetic */
    @keyframes scan {
        0% { border-top: 1px solid #00f0ff; }
        50% { border-top: 5px solid #00f0ff; }
        100% { border-top: 1px solid #00f0ff; }
    }
    header {
        border-bottom: 1px solid #00f0ff;
        animation: scan 2s infinite;
    }
    /* Login/Register Styling */
    .auth-container {
        max-width: 400px;
        margin: 50px auto;
        padding: 30px;
        background: rgba(10, 25, 47, 0.9);
        border: 2px solid #00f0ff;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.3);
    }
    .auth-title {
        text-align: center;
        margin-bottom: 30px;
    }
    /* Full screen background for login */
    .stApp:has(.auth-container) {
        background: radial-gradient(circle, #1a1c24 0%, #0e1117 100%);
    }
</style>
""", unsafe_allow_html=True)

# ===============================
# INIT DATABASE
# ===============================
init_db()
ensure_admin_exists()

# ===============================
# CONSTANTS
# ===============================
LABELS = ["Drone", "Aircraft", "Bird", "Helicopter", "Missile", "Clutter"]

PRIORITY = {
    "Drone": "High",
    "Aircraft": "Medium",
    "Bird": "Low",
    "Helicopter": "High",
    "Missile": "Critical",
    "Clutter": "Low"
}

# ===============================
# SESSION STATE
# ===============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.history = []
    st.session_state.auth_mode = "login"

if "tracker" not in st.session_state:
    tracker_cfg = cfg.get('tracker', {})
    st.session_state.tracker = MultiTargetTracker(tracker_cfg)
    st.session_state.tracker_enabled = tracker_cfg.get('enabled', True)

if "cognitive_controller" not in st.session_state:
    ctrl_cfg = cfg.get('cognitive_controller', {})
    st.session_state.cognitive_controller = CognitiveRadarController(ctrl_cfg)
    st.session_state.controller_enabled = ctrl_cfg.get('enabled', True)
    st.session_state.manual_override = False

if "ew_defense" not in st.session_state:
    ew_cfg = cfg.get('ew_defense', {})
    st.session_state.ew_defense = EWDefenseController(ew_cfg)
    st.session_state.ew_enabled = ew_cfg.get('enabled', True)

if "track_history" not in st.session_state:
    st.session_state.track_history = []
if "sensitivity_offset" not in st.session_state:
    st.session_state.sensitivity_offset = 0.0

if "tamper_detector" not in st.session_state:
    td = TamperDetector()
    # Add files to monitor
    # td.add_critical_file("app.py") # Disabled during dev to prevent self-triggering
    try:
        td.add_critical_file("src/model_pytorch.py")
        td.add_critical_file("src/ew_defense.py")
    except:
        pass
    td.establish_baseline_batch(["app.py"])
    st.session_state.tamper_detector = td
    st.session_state.tamper_check_timer = time.time()

if "ai_hardening" not in st.session_state:
    st.session_state.ai_hardening = {
        'conf_estimator': ConfidenceEstimator(),
        'ood_detector': OutOfDistributionDetector(method='entropy', threshold=0.6)
    }


# ===============================
# LOAD PYTORCH MODEL
# ===============================
@st.cache_resource
def load_model():
    # respect startup GPU availability
    use_cuda = _startup.get("gpu_available", False) and torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    radar_model = build_pytorch_model(num_classes=len(LABELS))
    model_path = safe_path("radar_model_pytorch.pt")
    if os.path.exists(model_path):
        try:
            state_dict = torch.load(model_path, map_location=device, weights_only=True)
            radar_model.load_state_dict(state_dict)
            st.success("✅ Radar AI model weights loaded successfully.")
        except Exception as e:
            st.error(f"Error loading model weights: {e}")
    else:
        st.warning("⚠️ Model weights not found in results/. Using untrained model.")
    
    radar_model.to(device)
    radar_model.eval()
    return radar_model, device

radar_model, device = load_model()

if 'real_loader' not in st.session_state:
    from src.data_loader_real import RealDataLoader
    st.session_state.real_loader = RealDataLoader()

# ===============================
# AUTHENTICATION CONTROL FLOW
# ===============================
if not st.session_state.logged_in:
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    if st.session_state.auth_mode == "login":
        st.markdown('<h1 class="auth-title">🔐 SECURITY CLEARANCE</h1>', unsafe_allow_html=True)
        with st.form("login"):
            username = st.text_input("Operator ID")
            password = st.text_input("Access Code", type="password")
            
            # 2D/3D Mode Selection at Logic
            viz_mode = st.radio("Visualization Mode", ["3D Immersive (High Fidelity)", "2D Performance (Fast)"], index=0)

            if st.form_submit_button("AUTHORIZE"):
                ok, role = authenticate(username, password)
                if ok:
                    st.session_state.logged_in = True
                    
                    # Set performance mode based on selection
                    if "2D" in viz_mode:
                        st.session_state.perf_mode = True
                    else:
                        st.session_state.perf_mode = False

                    st.session_state.user = username
                    st.session_state.role = role
                    st.success("✅ AUTHORIZED. ACCESS GRANTED.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ AUTHORIZATION DENIED")
        
        if st.button("New Operator? Register Here"):
            st.session_state.auth_mode = "register"
            st.rerun()

    else:
        st.markdown('<h1 class="auth-title">📝 OPERATOR REGISTRATION</h1>', unsafe_allow_html=True)
        from src.auth import register_user
        with st.form("register"):
            new_user = st.text_input("Choose Operator ID")
            new_pass = st.text_input("Set Access Code", type="password")
            confirm_pass = st.text_input("Confirm Access Code", type="password")
            role = st.selectbox("Assigned Role", ["viewer", "analyst"])
            
            if st.form_submit_button("REGISTER"):
                if not new_user or not new_pass:
                    st.error("Fields cannot be empty")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match")
                else:
                    success, msg = register_user(new_user, new_pass, role)
                    if success:
                        st.success("✅ Registration Successful. Please login.")
                        st.session_state.auth_mode = "login"
                        # No st.rerun here to let user see success message
                    else:
                        st.error(f"❌ {msg}")
        
        if st.button("Back to Login"):
            st.session_state.auth_mode = "login"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ===============================
# MAIN DASHBOARD (ONLY RENDERED AFTER LOGIN)
# ===============================
# ===============================
# SIDEBAR
# ===============================
st.sidebar.image("https://img.icons8.com/neon/96/radar.png", width=80)
st.sidebar.title("🛰️ COMMAND")
st.sidebar.write(f"👤 **Operator:** {st.session_state.user}")
st.sidebar.write(f"🔑 **Role:** {st.session_state.role}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

animate = st.sidebar.checkbox("Enable Animation", True)

# PERFORMANCE MODE (Moved to top of file for global scope access)
perf_mode = st.session_state.get("perf_mode", False)


gain = st.sidebar.slider("Gain (dB)", 1, 40, 15)
distance = st.sidebar.slider("Distance (m)", 10, 1000, 200)
source = st.sidebar.radio("Signal Source", ["Simulated", "RTL-SDR", "Real Data (77GHz)"])

if source == "RTL-SDR":
    st.sidebar.warning("🎯 Target Type is ignored in RTL-SDR mode (using live data)")
    target = st.sidebar.selectbox("Target Type (Disabled)", LABELS, disabled=True, key="target_type_disabled")
elif source == "Real Data (77GHz)":
    st.sidebar.info("📂 Using Zenodo Dataset (Drones/Birds)")
    target = st.sidebar.selectbox("Target Type (Disabled)", LABELS, disabled=True, key="target_type_real")
else:
    target = st.sidebar.selectbox("Target Type", LABELS, key="target_type_active")

# ===============================
# DASHBOARD
# ===============================
# Enhanced Header
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("")

with col2:
    st.markdown("""
    <div style='text-align: center; margin: 20px 0;'>
        <h1 style='margin: 0; font-size: 2.8rem;'>🛰️ PHOENIX-RADAR COMMAND CENTER</h1>
        <p style='color: #a0b4ff; letter-spacing: 2px; margin-top: 10px; font-size: 0.95rem;'>
            ⚡ AI-Enabled Cognitive Defense System | Real-Time Threat Detection & Tracking
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("")

# Status Bar
status_col1, status_col2, status_col3, status_col4 = st.columns(4)

try:
    import psutil
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
except:
    cpu_usage = 0
    memory_usage = 0

with status_col1:
    status = "🟢 ACTIVE" if st.session_state.logged_in else "🔴 OFFLINE"
    st.metric("System Status", status, border=True)

with status_col2:
    st.metric("CPU Usage", f"{cpu_usage:.1f}%", border=True)

with status_col3:
    st.metric("Memory", f"{memory_usage:.1f}%", border=True)

with status_col4:
    st.metric("Operator", st.session_state.user, border=True)

# Periodically check integrity
if time.time() - st.session_state.get('tamper_check_timer', 0) > 60:
    st.session_state.tamper_detector.check_all_critical_files()
    st.session_state.tamper_check_timer = time.time()

unresolved = st.session_state.tamper_detector.get_unresolved_events()
if unresolved:
    st.error(f"🚨 SECURITY ALERT: {len(unresolved)} Integrity Violations Detected!")

st.markdown("---")

# Create Professional Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Real-Time Analytics", "🧠 Explainable AI", "⚙️ System Config", "📋 Logs", "👨‍💼 Admin"]
)

# ===============================
# PRE-PROCESSING FOR ANALYTICS (Needed for XAI too)
# ===============================
target_low = target.lower()

if source == "RTL-SDR":
    from src.rtl_sdr_receiver import HAS_RTLSDR
    if not HAS_RTLSDR:
        st.error("RTL-SDR Library (librtlsdr) not found. Falling back to simulation.")
        signal = generate_radar_signal(target_low, distance)
    else:
        try:
            sdr = RTLRadar()
            signal = sdr.read_samples(4096)
            sdr.close()
        except Exception as e:
            st.error(f"SDR Hardware Error: {e}. Falling back to simulation.")
            signal = generate_radar_signal(target_low, distance)
elif source == "Real Data (77GHz)":
    # Try to get next sample from loader
    sample = st.session_state.real_loader.get_next_sample()
    
    if sample is None:
        # Check if file actually exists to give better feedback
        if not os.path.exists(st.session_state.real_loader.data_path):
            st.error(f"❌ Real dataset file not found at: {st.session_state.real_loader.data_path}")
            st.info("Please download the dataset manually or check the path.")
        else:
            st.error("❌ Failed to load dataset (unknown error). Check logs.")
            
        st.warning("⚠️ Falling back to simulation.")
        signal = generate_radar_signal(target_low, distance)
    else:
        st.success(f"✅ DATA LOADED: Using sample from Zenodo Dataset (Shape: {sample.shape})")
        # Ensure sample matches expected signal shape (4096,) for processing
        # The dataset might be 2D chips, so we might need to flatten or select a row
        if len(sample.shape) > 1:
             # Basic adaptation: take the first row or flatten if small enough
             signal = sample.flatten()[:4096]
        else:
             signal = sample[:4096]
             
        # Pad if too short
        if len(signal) < 4096:
            st.warning(f"Sample too short ({len(signal)}), padding with zeros.")
            signal = np.pad(signal, (0, 4096 - len(signal)))
            
        # Normalize
        signal = signal / (np.max(np.abs(signal)) + 1e-9)
        signal *= 10 ** (gain / 20)
else:
    signal = generate_radar_signal(target_low, distance)

signal *= 10 ** (gain / 20)

try:
    # Run classical detection chain and only run AI if CFAR finds detections
    # Using cached wrapper
    detect_res = cached_detect_targets(signal, fs=4096, n_range=128, n_doppler=128, method='ca', guard=2, train=8, pfa=1e-4)
    rd_map = detect_res['rd_map']
    spec, meta, photonic = None, None, None

    # Always compute features for UI / photonic params
    # Optimization: Pass pre-computed rd_map to avoid redundant FFT
    # Using cached wrapper
    rd_map, spec, meta, photonic = cached_get_all_features(signal, rd_map=rd_map)

    detections = detect_res.get('detections', [])
    ai_results = []
    
    IMG_SIZE = 128
    det_cfg = cfg.get('detection', {})
    crop_size = int(det_cfg.get('crop_size', 32))

    if len(detections) > 0:
        log_event(f"Processing {len(detections)} CFAR detections in AI pipeline", level="info")
        # ensure spectrogram aligns with rd_map dimensions for cropping
        try:
            spec_resized_full = cv2.resize(spec, (rd_map.shape[1], rd_map.shape[0]))
        except Exception:
            spec_resized_full = np.abs(spec)

        half = crop_size // 2
        batch_rd = []
        batch_spec = []
        batch_meta = []
        batch_indices = []

        # First pass: Collect valid crops
        for idx_det, det in enumerate(detections):
            i, j, val = det
            i = int(i); j = int(j)

            try:
                # pad rd_map and spec if crop goes out of bounds
                pad_y = max(0, half - i, (i + half) - rd_map.shape[0] + 1)
                pad_x = max(0, half - j, (j + half) - rd_map.shape[1] + 1)
                
                if pad_x > 0 or pad_y > 0:
                    rd_pad = np.pad(rd_map, ((pad_y, pad_y), (pad_x, pad_x)), mode='constant')
                    spec_pad = np.pad(spec_resized_full, ((pad_y, pad_y), (pad_x, pad_x)), mode='constant')
                    i_adj = i + pad_y
                    j_adj = j + pad_x
                else:
                    rd_pad = rd_map
                    spec_pad = spec_resized_full
                    i_adj = i
                    j_adj = j

                y1 = i_adj - half; y2 = i_adj + half
                x1 = j_adj - half; x2 = j_adj + half
                
                # Double check bounds
                if y1 < 0 or x1 < 0 or y2 > rd_pad.shape[0] or x2 > rd_pad.shape[1]:
                    continue

                rd_crop = rd_pad[y1:y2, x1:x2]
                spec_crop = spec_pad[y1:y2, x1:x2]
                
                if rd_crop.size == 0 or spec_crop.size == 0:
                    continue

                # Resize to model input
                rd_img = cv2.resize(rd_crop.astype(np.float32), (IMG_SIZE, IMG_SIZE))
                spec_img = cv2.resize(spec_crop.astype(np.float32), (IMG_SIZE, IMG_SIZE))

                # Normalize (Standardize)
                rd_std = np.std(rd_img) + 1e-8
                spec_std = np.std(spec_img) + 1e-8
                rd_norm_local = (rd_img - np.mean(rd_img)) / rd_std
                spec_norm_local = (spec_img - np.mean(spec_img)) / spec_std

                batch_rd.append(rd_norm_local)
                batch_spec.append(spec_norm_local)
                batch_meta.append(meta)
                batch_indices.append(idx_det)
            
            except Exception as e:
                # Log specific error but don't crash
                # log_event(f"Error processing detection crop: {e}", level="warning")
                continue

        # Batch Inference
        if len(batch_rd) > 0:
            try:
                # Stack into [B, 1, IMG_SIZE, IMG_SIZE]
                rd_t_batch = torch.from_numpy(np.array(batch_rd)).float().unsqueeze(1).to(device)
                spec_t_batch = torch.from_numpy(np.array(batch_spec)).float().unsqueeze(1).to(device)
                meta_t_batch = torch.from_numpy(np.array(batch_meta)).float().to(device)

                with torch.no_grad():
                    out_batch = radar_model(rd_t_batch, spec_t_batch, meta_t_batch)
                    
                    # AI Hardening: Confidence & OOD
                    ce = st.session_state.ai_hardening['conf_estimator']
                    ood = st.session_state.ai_hardening['ood_detector']
                    
                    # Estimate confidence for batch (assuming CE supports batch, otherwise loop)
                    # Check if CE supports batch. If not, simple softmax here.
                    # Standard softmax for batch
                    ps_batch = torch.softmax(out_batch, dim=1)
                    
                    # Process results
                    for k, idx_det in enumerate(batch_indices):
                        out_single = out_batch[k:k+1] # Keep batch dim for compatibility
                        
                        # Use existing hardening objects (assuming they handle single items)
                        conf, entropy = ce.estimate(out_single)
                        is_ood, ood_score = ood.detect(out_single)
                        
                        ps = ps_batch[k]
                        cls_idx = int(torch.argmax(ps))
                        label = LABELS[cls_idx] if cls_idx < len(LABELS) else 'Clutter'
                        
                        det_orig = detections[idx_det]
                        
                        ai_results.append({
                            "det": (det_orig[0], det_orig[1]), 
                            "label": label, 
                            "confidence": conf, 
                            "value": det_orig[2],
                            "entropy": entropy,
                            "is_ood": is_ood,
                            "ood_score": ood_score
                        })
            except Exception as e:
                st.error(f"Batch inference failed: {e}")
                log_event(f"Batch inference error: {e}", level="error")

        # choose highest-confidence detection for top-level UI
        best = max(ai_results, key=lambda x: x['confidence']) if ai_results else None
        if best is not None:
            detected = best['label']
            confidence = best['confidence']
        else:
            detected = "Clutter"
            confidence = 0.0

    else:
        log_event("No CFAR detections found; skipping AI inference", level="info")
        detected = "Clutter"
        confidence = 0.0

    # ===== MULTI-TARGET TRACKING =====
    if st.session_state.tracker_enabled:
        # Convert AI results to tracker detections: (range_idx, doppler_idx, value)
        tracker_detections = [(res['det'][0], res['det'][1], res['confidence']) for res in ai_results]
        
        # Update multi-target tracker
        active_tracks = st.session_state.tracker.update(tracker_detections)
        
        if active_tracks:
            log_event(f"Tracking: {len(active_tracks)} active targets", level="info")
        
        # Store track history for UI
        if not hasattr(st.session_state, 'track_history'):
            st.session_state.track_history = []
        st.session_state.track_history.append({
            'time': time.time(),
            'tracks': active_tracks,
            'detected': detected,
            'confidence': confidence
        })
        # Keep last 100 updates
        st.session_state.track_history = st.session_state.track_history[-100:]
    else:
        active_tracks = {}

    # ===== ELECTRONIC WARFARE DEFENSE =====
    if st.session_state.ew_enabled:
        ai_labels = [res['label'] for res in ai_results]
        ai_confidences = [res['confidence'] for res in ai_results]
        
        ew_result = st.session_state.ew_defense.analyze(
            signal=signal,
            detections=detections,
            ai_labels=ai_labels,
            ai_confidences=ai_confidences
        )
        
        if ew_result['ew_active']:
            log_event(f"EW ALERT: Threat level {ew_result['threat_level']}, {len(ew_result['threats'])} threats detected", level="warning")
            for threat in ew_result['threats']:
                log_event(f"  - {threat.threat_type}: conf={threat.confidence:.2f}, sev={threat.severity}", level="warning")
            for cm in ew_result['countermeasures']:
                log_event(f"  ⚡ Countermeasure: {cm.action_type} ({cm.reason})", level="info")
        
        # Filter detections: only keep real detections
        if ew_result['real_detections']:
            ai_results_filtered = [res for res, is_real in zip(ai_results, ew_result['real_detections']) if is_real]
        else:
            ai_results_filtered = ai_results
    else:
        ew_result = {'threats': [], 'ew_active': False, 'threat_level': 'green', 'real_detections': None}
        ai_results_filtered = ai_results

    # ===== COGNITIVE CONTROL ADAPTATION =====
    if st.session_state.controller_enabled:
        # Compute confidence metrics (use filtered detections if EW active)
        det_results = ai_results_filtered if st.session_state.ew_enabled and ew_result['real_detections'] else ai_results
        avg_det_conf = np.mean([res['confidence'] for res in det_results]) if det_results else 0.0
        avg_trk_conf = np.mean([t['confidence'] for t in active_tracks.values()]) if active_tracks else 0.0
        num_tracks = len([t for t in active_tracks.values() if t['state'] == 'confirmed'])
        false_positives = len(detections) - len(det_results) if len(detections) > len(det_results) else 0
        
        # Observe state
        curr_state = st.session_state.cognitive_controller.observe(
            detection_confidence=avg_det_conf,
            tracking_confidence=avg_trk_conf,
            num_active_tracks=num_tracks,
            total_detections=len(detections),
            false_positives=false_positives,
            current_gain=gain,
            max_gain=40.0
        )
        
        # Learn from previous observation
        reward = st.session_state.cognitive_controller.learn(curr_state)
        
        # Decide next action (waveform parameters)
        cognitive_action = st.session_state.cognitive_controller.decide(curr_state)
        
        # Apply cognitive action if not in manual override
        if cognitive_action.is_adaptive:
            gain = cognitive_action.gain_db
            distance = cognitive_action.distance_m
            target = cognitive_action.target_type
            log_event(f"Cognitive adaptation: gain={gain:.1f}dB, dist={distance:.0f}m, target={target}", level="info")

    rd_map_resized = cv2.resize(rd_map, (128, 128))
    spec_resized = cv2.resize(spec, (128, 128))

    rd_norm = rd_map_resized / (np.max(rd_map_resized) + 1e-8)
    spec_norm = spec_resized / (np.max(spec_resized) + 1e-8)
    rd_t = torch.from_numpy(rd_norm).float().unsqueeze(0).unsqueeze(0).to(device) # (1, 1, 128, 128)
    spec_t = torch.from_numpy(spec_norm).float().unsqueeze(0).unsqueeze(0).to(device) # (1, 1, 128, 128)
    meta_t = torch.from_numpy(meta).float().unsqueeze(0).to(device)
    with torch.no_grad():
        output = radar_model(rd_t, spec_t, meta_t)
        probs = torch.softmax(output, dim=1)
        confidence = float(torch.max(probs))
        detected_idx = int(torch.argmax(probs))
        detected = LABELS[detected_idx] if detected_idx < len(LABELS) else "Clutter"

    st.session_state.track_history = st.session_state.track_history[-50:]

    # Cognitive threshold
    thresh = adaptive_threshold(photonic['noise_power']) + st.session_state.get('sensitivity_offset', 0.0)
    is_alert = confidence > thresh

    # Kafka Streaming (Optional)
    if "kafka_producer" not in st.session_state:
        st.session_state.kafka_producer = get_producer()

    try:
        producer = st.session_state.kafka_producer
        if producer:
            producer.send("radar-stream", {
                "time": time.time(),
                "target": detected,
                "confidence": float(confidence),
                "distance": float(distance)
            })
    except Exception:
        pass

except Exception as e:
    st.error(f"Processing Error: {e}")
    log_event(f"CRITICAL PIPELINE ERROR: {str(e)}", level="error")
    # Set default values so UI doesn't crash
    detected = "Error"
    confidence = 0.0
    rd_map = np.zeros((128, 128))
    spec = np.zeros((128, 128))
    meta = np.zeros(8)
    active_tracks = {}
    is_alert = False
    thresh = 0.5
    photonic = {'noise_power': 0, 'clutter_power': 0, 'instantaneous_bandwidth': 0, 'chirp_slope': 0, 'pulse_width': 0, 'ttd_vector': []}


# ===============================
# TAB 1: ANALYTICS
# ===============================
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        # 3D VISUALIZATION UPGRADE
        st.subheader("Interactive Radar Analysis")
        
        rd_db = 10 * np.log10(rd_map + 1e-12)
        
        # Color mapping for targets
        COLOR_MAP = {
            "Drone": "#FFA500",      # Orange
            "Aircraft": "#00FFFF",   # Cyan
            "Bird": "#00FF00",       # Green
            "Helicopter": "#FF00FF", # Magenta
            "Missile": "#FF0000",    # Red
            "Clutter": "#808080"     # Gray
        }

        # Container for plot to ensure clean replacement
        plot_container = st.empty()
        
        with plot_container:
            if perf_mode:
                # FAST 2D HEATMAP
                # Downsample for speed if needed, but 128x128 is usually fine for 2D
                fig_rd_3d = go.Figure(data=go.Heatmap(
                    z=rd_db,
                    colorscale='Viridis',
                    zmin=-30, zmax=30,
                    hoverinfo='z'
                ))
                
                # Add markers to 2D view using Classification Results (ai_results)
                if 'ai_results' in locals() and ai_results:
                    for res in ai_results:
                        r_idx, d_idx = res['det']
                        label = res['label']
                        conf = res['confidence'] * 100
                        color = COLOR_MAP.get(label, "#FFFFFF")
                        
                        fig_rd_3d.add_trace(go.Scatter(
                            x=[d_idx], y=[r_idx],
                            mode='markers+text',
                            marker=dict(size=14, color=color, symbol='circle-open', line=dict(width=3, color=color)),
                            text=[f"{label}"],
                            textposition="top center",
                            textfont=dict(color=color, size=12, family="Orbitron"),
                            hoverinfo='text',
                            hovertext=f"Type: {label}<br>Conf: {conf:.1f}%<br>R: {r_idx}, D: {d_idx}",
                            name=label,
                            showlegend=False
                        ))
                # Fallback to raw detections if no AI results yet (or if AI disabled/failed)
                elif detections:
                    det_x = [d[1] for d in detections]
                    det_y = [d[0] for d in detections]
                    fig_rd_3d.add_trace(go.Scatter(
                        x=det_x, y=det_y,
                        mode='markers',
                        marker=dict(size=10, color='rgba(255, 50, 50, 0.8)', symbol='circle-open', line=dict(width=2)),
                        name='Unclassified'
                    ))

                fig_rd_3d.update_layout(
                    title='Range-Doppler Map (2D) - Target ID',
                    xaxis_title='Doppler',
                    yaxis_title='Range',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#00f0ff'),
                    margin=dict(l=0, r=0, b=0, t=30),
                    height=400
                )
                # Unique key prevents ghosting
                st.plotly_chart(fig_rd_3d, use_container_width=True, key=f"rd_2d_{perf_mode}")
            else:
                # FULL 3D SURFACE
                fig_rd_3d = go.Figure(data=[go.Surface(
                    z=rd_db, 
                    colorscale='Viridis', 
                    contours_z=dict(show=True, usecolormap=True, highlightcolor="limegreen", project_z=True),
                    opacity=0.9
                )])
                
                # Overlay Detections (3D) with ID
                if 'ai_results' in locals() and ai_results:
                    for res in ai_results:
                        r_idx, d_idx = res['det']
                        label = res['label']
                        conf = res['confidence'] * 100
                        color = COLOR_MAP.get(label, "#FFFFFF")
                        z_val = rd_db[int(r_idx), int(d_idx)] + 10
                        
                        fig_rd_3d.add_trace(go.Scatter3d(
                            x=[d_idx], y=[r_idx], z=[z_val],
                            mode='markers+text',
                            marker=dict(size=12, color=color, symbol='circle', line=dict(color='white', width=2)),
                            text=[f"{label}"],
                            textposition="top center",
                            textfont=dict(color=color, size=14, family="Orbitron"),
                            hovertext=f"Type: {label}<br>Conf: {conf:.1f}%",
                            hoverinfo='text',
                            name=label
                        ))
                elif detections:
                    det_x = [d[1] for d in detections]  # Doppler
                    det_y = [d[0] for d in detections]  # Range
                    det_z = [rd_db[int(d[0]), int(d[1])] + 10 for d in detections] # Lift above surface explicitly
                    
                    fig_rd_3d.add_trace(go.Scatter3d(
                        x=det_x, y=det_y, z=det_z,
                        mode='markers',
                        marker=dict(size=10, color='rgba(255, 30, 30, 0.9)', symbol='circle', line=dict(color='rgba(255, 200, 200, 1.0)', width=2)),
                        name='Detected Target'
                    ))

                fig_rd_3d.update_layout(
                    title='3D Range-Doppler Map - Enhanced ID',
                    autosize=True,
                    scene=dict(
                        xaxis_title='Doppler',
                        yaxis_title='Range',
                        zaxis_title='Intensity (dB)',
                        xaxis=dict(gridcolor='rgba(0, 240, 255, 0.2)'),
                        yaxis=dict(gridcolor='rgba(0, 240, 255, 0.2)'),
                        zaxis=dict(gridcolor='rgba(0, 240, 255, 0.2)'),
                        bgcolor="rgba(0,0,0,0)"
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#00f0ff'),
                    margin=dict(l=0, r=0, b=0, t=30),
                    height=500,
                    scene_camera=dict(eye=dict(x=1.6, y=1.6, z=1.2))
                )
                # Unique key prevents ghosting
                st.plotly_chart(fig_rd_3d, use_container_width=True, key=f"rd_3d_{perf_mode}")

                


        # 2. Spectrogram
        spec_db = 10 * np.log10(spec + 1e-12)
        
        spec_container = st.empty()
        with spec_container:
            if perf_mode:
                # FAST 2D HEATMAP
                fig_spec_3d = go.Figure(data=go.Heatmap(
                    z=spec_db,
                    colorscale='Magma',
                    zmin=-30, zmax=30
                ))
                fig_spec_3d.update_layout(
                    title='Micro-Doppler Spectrogram (2D)',
                    xaxis_title='Time',
                    yaxis_title='Frequency',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#bc13fe'),
                    margin=dict(l=0, r=0, b=0, t=30),
                    height=400
                )
                st.plotly_chart(fig_spec_3d, use_container_width=True, key=f"spec_2d_{perf_mode}")
            else:
                fig_spec_3d = go.Figure(data=[go.Surface(
                    z=spec_db, 
                    colorscale='Magma', 
                    opacity=0.9
                )])
                fig_spec_3d.update_layout(
                    title='3D Micro-Doppler Spectrogram',
                    autosize=True,
                    scene=dict(
                        xaxis_title='Time',
                        yaxis_title='Frequency',
                        zaxis_title='Intensity (dB)',
                        xaxis=dict(gridcolor='rgba(188, 19, 254, 0.2)'),
                        yaxis=dict(gridcolor='rgba(188, 19, 254, 0.2)'),
                        zaxis=dict(gridcolor='rgba(188, 19, 254, 0.2)'),
                        bgcolor="rgba(0,0,0,0)"
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#bc13fe'),
                    margin=dict(l=0, r=0, b=0, t=30),
                    height=500
                )
                st.plotly_chart(fig_spec_3d, use_container_width=True, key=f"spec_3d_{perf_mode}")

        # Tracking Plot (3D Upgrade)
        st.subheader("🎯 Target Tracking (Kalman Filter) — 3D View")
        if st.session_state.track_history and len(st.session_state.track_history) > 0:
            # Extract position data from track history
            hx, hy = [], []
            for entry in st.session_state.track_history:
                if 'tracks' in entry and entry['tracks']:
                    for track_id, track_data in entry['tracks'].items():
                        if 'position' in track_data:
                            x, y = track_data['position']
                            hx.append(x)
                            hy.append(y)
            
            if hx and hy:
                hz = list(range(len(hx)))  # simple time index for z-axis
                fig3d = go.Figure()
                fig3d.add_trace(go.Scatter3d(x=hx, y=hy, z=hz, mode='lines+markers',
                                             line=dict(color='lime', width=4),
                                             marker=dict(size=4, color='cyan')))
                fig3d.update_layout(scene=dict(xaxis_title='X Position (m)',
                                               yaxis_title='Y Position (m)',
                                               zaxis_title='Time Index'),
                                    margin=dict(l=0, r=0, t=30, b=0),
                                    height=400, paper_bgcolor='rgba(0,0,0,0)',
                                    font=dict(color='#00f0ff'))
                st.plotly_chart(fig3d, use_container_width=True)
            else:
                st.info("No track positions available yet.")
        else:
            st.info("No tracking history yet — generate data to populate 3D track view.")

    with col2:
        if is_alert:
            st.error(f"🚨 ALERT: {detected} Detected!")
        else:
            st.info("Searching for targets...")

        st.metric("Detected Target", detected)
        
        # Threat Level Gauge
        threat_color = "green"
        if PRIORITY[detected] == "High": threat_color = "orange"
        if PRIORITY[detected] == "Critical": threat_color = "red"

        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = confidence * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"THREAT LEVEL: {PRIORITY[detected]}", 'font': {'size': 18}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': threat_color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(0, 255, 0, 0.3)'},
                    {'range': [50, 80], 'color': 'rgba(255, 255, 0, 0.3)'},
                    {'range': [80, 100], 'color': 'rgba(255, 0, 0, 0.3)'}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': thresh * 100}
            }
        ))
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                font={'color': "#00ff41", 'family': "Courier New"},
                                height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, width='stretch')

        st.write(f"Confidence: {confidence * 100:.2f}%")
        st.write(f"Cognitive Threshold: {thresh:.2f}")
        st.write(f"Priority: **{PRIORITY[detected]}**")

        st.markdown("---")
        st.subheader("📋 Active Targets")
        if 'ai_results' in locals() and ai_results:
            target_list_data = []
            for res in ai_results:
                target_list_data.append({
                    "Type": res['label'],
                    "Range": f"{res['det'][0]}", # Just index for now
                    "Conf": f"{res['confidence']*100:.0f}%"
                })
            
            st.table(pd.DataFrame(target_list_data))
        else:
            st.caption("No classified targets")

        st.markdown("---")
        st.subheader("Phase Statistics")
        if len(meta) >= 3:
            st.write(f"Mean Phase: {meta[0]:.4f}")
            st.write(f"Variance: {meta[1]:.4f}")
            st.write(f"Coherence: {meta[2]:.4f}")
        else:
            st.write("Metadata incomplete")

# ===============================
# TAB 2: XAI
# ===============================
with tab2:
    st.subheader("Explainable AI: Grad-CAM Visualizations")
    st.write("Visualizing which parts of the input maps influenced the AI's decision.")
    
    try:
        col_xai1, col_xai2 = st.columns(2)
        
        # Compute Grad-CAM for both branches
        grad_cam_result_rd = grad_cam_pytorch(radar_model, rd_t, spec_t, meta_t, radar_model.rd_branch.conv2)
        grad_cam_result_spec = grad_cam_pytorch(radar_model, rd_t, spec_t, meta_t, radar_model.spec_branch.conv2)

        with col_xai1:
            st.write("**RD Map Heatmap**")
            if grad_cam_result_rd is not None:
                cam_rd, rd_success = grad_cam_result_rd
                if rd_success and np.any(cam_rd):
                    fig_rd, ax_rd = plt.subplots()
                    ax_rd.imshow(rd_norm, cmap='gray')
                    ax_rd.imshow(cam_rd, cmap='jet', alpha=0.5)
                    ax_rd.set_title("RD Map Grad-CAM")
                    st.pyplot(fig_rd)
                else:
                    st.info("Grad-CAM unavailable - showing RD Map")
                    st.image(rd_norm, caption="RD Map", use_container_width=True, channels='GRAY')
            else:
                st.image(rd_norm, caption="RD Map", use_container_width=True, channels='GRAY')

        with col_xai2:
            st.write("**Spectrogram Heatmap**")
            if grad_cam_result_spec is not None:
                cam_spec, spec_success = grad_cam_result_spec
                if spec_success and np.any(cam_spec):
                    fig_sp, ax_sp = plt.subplots()
                    ax_sp.imshow(spec_norm, cmap='gray')
                    ax_sp.imshow(cam_spec, cmap='jet', alpha=0.5)
                    ax_sp.set_title("Spectrogram Grad-CAM")
                    st.pyplot(fig_sp)
                else:
                    st.info("Grad-CAM unavailable - showing Spectrogram")
                    st.image(spec_norm, caption="Spectrogram", use_container_width=True, channels='GRAY')
            else:
                st.image(spec_norm, caption="Spectrogram", use_container_width=True, channels='GRAY')
    except Exception as e:
        st.error(f"XAI Visualization Error: {e}")
        st.info("Showing raw input maps instead...")
        col_xai1, col_xai2 = st.columns(2)
        with col_xai1:
            st.image(rd_norm, caption="RD Map", use_container_width=True, channels='GRAY')
        with col_xai2:
            st.image(spec_norm, caption="Spectrogram", use_container_width=True, channels='GRAY')

# ===============================
# TAB 3: PHOTONIC PARAMETERS
# ===============================
with tab3:
    st.subheader("Photonic Radar Parameters")

    st.write(f"Bandwidth: {photonic['instantaneous_bandwidth']/1e6:.2f} MHz")
    st.write(f"Chirp Slope: {photonic['chirp_slope']/1e12:.2f} THz/s")
    st.write(f"Pulse Width: {photonic['pulse_width']*1e6:.2f} μs")
    st.write(f"Noise Power: {photonic['noise_power']:.6f}")
    st.write(f"Clutter Power: {photonic['clutter_power']:.6f}")

    st.markdown("#### TTD Beamforming Vector")
    st.line_chart(photonic["ttd_vector"])

# ===============================
# TAB 4: LOGS
# ===============================
with tab4:
    st.subheader("Detection History")

    # Only add to history if something interesting happened or periodically
    # To avoid infinite growth during animation, we limit how often we log.
    if "last_log_time" not in st.session_state:
        st.session_state.last_log_time = 0
    
    current_time = time.time()
    if current_time - st.session_state.last_log_time > 2.0: # Log every 2 seconds
        entry = {
            "Time": time.strftime("%H:%M:%S"),
            "Target": detected,
            "Confidence": f"{confidence*100:.1f}%",
            "Priority": PRIORITY[detected]
        }
        st.session_state.history.append(entry)
        # Optimization: Cap history to prevent memory leak
        if len(st.session_state.history) > 1000:
            st.session_state.history = st.session_state.history[-1000:]

        st.session_state.last_log_time = current_time
        
        if is_alert:
            log_event(f"ALERT: {detected} detected with {confidence*100:.1f}% confidence")

    df = pd.DataFrame(st.session_state.history[-20:])
    st.table(df)

    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Threat Report (CSV)",
            data=csv,
            file_name=f"radar_report_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv',
        )

    st.markdown("#### System Logs")
    st.code("".join(read_logs(20)))

# ===============================
# TAB 5: ADMIN PANEL
# ===============================
with tab5:
    if st.session_state.role != "admin":
        st.warning("⚠️ Access Denied: Admin privileges required.")
    else:
        st.subheader("🛠️ Administrative Controls")
        
        admin_subtab1, admin_subtab2, admin_subtab3, admin_subtab4 = st.tabs(["User Management", "System Health", "Advanced Config", "Security Audit"])
        
        with admin_subtab1:
            from src.user_manager import list_users, create_user, delete_user, update_user_role
            
            st.markdown("### User Management")
            users = list_users()
            user_df = pd.DataFrame(users, columns=["Username", "Role"])
            st.table(user_df)
            
            with st.expander("Add New User"):
                with st.form("add_user"):
                    new_user = st.text_input("Username")
                    new_pass = st.text_input("Password", type="password")
                    new_role = st.selectbox("Role", ["viewer", "operator", "admin"])
                    if st.form_submit_button("Create User"):
                        if new_user and new_pass:
                            create_user(new_user, new_pass, new_role)
                            st.success(f"User {new_user} created!")
                            st.rerun()
                        else:
                            st.error("Fields cannot be empty")
            
            with st.expander("Delete/Update User"):
                target_user = st.selectbox("Select User", [u[0] for u in users if u[0] != st.session_state.user])
                col_del, col_upd = st.columns(2)
                with col_del:
                    if st.button("Delete User", type="primary"):
                        delete_user(target_user)
                        st.success(f"User {target_user} deleted")
                        st.rerun()
                with col_upd:
                    new_role_val = st.selectbox("New Role", ["viewer", "operator", "admin"], key="new_role_val")
                    if st.button("Update Role"):
                        update_user_role(target_user, new_role_val)
                        st.success(f"Role updated for {target_user}")
                        st.rerun()

        with admin_subtab2:
            st.markdown("### System Health")
            if HAS_PSUTIL:
                cpu_usage = psutil.cpu_percent()
                mem_usage = psutil.virtual_memory().percent
            else:
                cpu_usage = "N/A"
                mem_usage = "N/A"
            
            col_h1, col_h2, col_h3 = st.columns(3)
            col_h1.metric("CPU Usage", f"{cpu_usage}%" if HAS_PSUTIL else "N/A")
            col_h2.metric("Memory Usage", f"{mem_usage}%" if HAS_PSUTIL else "N/A")
            col_h3.metric("DB Status", "Connected" if os.path.exists("results/users.db") else "Error")
            
            st.markdown("#### Hardware Status")
            from src.rtl_sdr_receiver import HAS_RTLSDR
            st.write(f"RTL-SDR Driver: {'✅ Detected' if HAS_RTLSDR else '❌ Missing'}")
            
            from src.stream_bus import HAS_KAFKA
            st.write(f"Kafka Integration: {'✅ Active' if HAS_KAFKA else '⚠️ Disabled (Library Missing)'}")

        with admin_subtab3:
            st.markdown("### Advanced Configuration")
            st.info("System-wide parameters (Require restart to take full effect)")
            new_threshold = st.slider("Global Sensitivity Offset", -0.2, 0.2, 0.0)
            st.session_state.sensitivity_offset = new_threshold
            
            if st.button("Clear System Logs", type="secondary"):
                with open("results/system.log", "w") as f:
                    f.write("")
                st.success("Logs cleared")
                st.rerun()

        with admin_subtab4:
            st.markdown("### Security & Integrity Audit")
            
            events = st.session_state.tamper_detector.get_tamper_events()
            if events:
                for i, event in enumerate(events):
                    e_dict = event.to_dict()
                    cols = st.columns([1, 4, 2])
                    with cols[0]:
                        if e_dict['severity'] == 'critical':
                            st.error(f"CRITICAL")
                        else:
                            st.warning(f"WARN")
                    with cols[1]:
                        st.write(f"**{e_dict['filepath']}**: {e_dict['reason']}")
                        st.caption(f"Time: {e_dict['timestamp']}")
                    with cols[2]:
                        if not e_dict['resolved']:
                            if st.button("Mark Resolved", key=f"resolve_{i}"):
                                st.session_state.tamper_detector.mark_event_resolved(i)
                                st.rerun()
                        else:
                            st.success("Resolved")
                    st.divider()
            else:
                st.success("✅ System Integrity Verified. No incidents.")
                
            if st.button("Run Integrity Check Now"):
                st.session_state.tamper_detector.check_all_critical_files()
                st.rerun()

# ===============================
# SAFE AUTO-REFRESH
# ===============================
if animate:
    # Adaptive sleep based on performance mode
    sleep_time = 1.0 if perf_mode else 0.5
    time.sleep(sleep_time)
    # Streamlit recommends using fragment for local updates or 
    # being careful with rerun in loops.
    # To prevent rapid-fire reruns that can cause "script already running" errors,
    # we ensure a minimum delay.
    st.rerun()
