
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path
import json
import random

# --- PROJECT ROOT SETUP ---
# Dashboard is at: photonic-radar-ai/ui/dashboard.py
# Need to add photonic-radar-ai (parent of ui) to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- CONFIGURATION ---
API_URL = "http://localhost:5000"
REFRESH_RATE = 1.0  # Seconds
API_TIMEOUT = 0.5  # Timeout for API calls in seconds

st.set_page_config(
    page_title="PHOENIX TACTICAL COMMAND",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- MILITARY TACTICAL THEME ---
st.markdown("""
    <style>
    /* Dark military background */
    .stApp {
        background-color: #0a0e14;
        color: #e0e0e0;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #4ade80 !important;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(74, 222, 128, 0.3);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1c24 0%, #0e1117 100%);
        border: 2px solid #4ade80;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 0 20px rgba(74, 222, 128, 0.2);
        margin: 10px 0;
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: bold;
        color: #4ade80;
        font-family: 'Courier New', monospace;
        text-shadow: 0 0 10px rgba(74, 222, 128, 0.5);
    }
    
    .metric-label {
        font-size: 11px;
        text-transform: uppercase;
        color: #888;
        letter-spacing: 1px;
        margin-top: 5px;
        font-family: 'Courier New', monospace;
    }
    
    /* Status indicators */
    .status-online {
        color: #4ade80;
        font-weight: bold;
    }
    
    .status-offline {
        color: #ef4444;
        font-weight: bold;
    }
    
    .status-waiting {
        color: #fbbf24;
        font-weight: bold;
    }
    
    /* Threat level colors */
    .threat-friendly {
        color: #4ade80 !important;
    }
    
    .threat-neutral {
        color: #fbbf24 !important;
    }
    
    .threat-unknown {
        color: #fb923c !important;
    }
    
    .threat-hostile {
        color: #ef4444 !important;
    }
    
    /* Priority badges */
    .priority-low {
        background-color: #166534;
        color: #4ade80;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 10px;
    }
    
    .priority-medium {
        background-color: #854d0e;
        color: #fbbf24;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 10px;
    }
    
    .priority-high {
        background-color: #7f1d1d;
        color: #ef4444;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 10px;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* Event ticker styling */
    .event-ticker {
        background-color: #1a1c24;
        border: 1px solid #4ade80;
        border-radius: 5px;
        padding: 10px;
        height: 350px;
        min-height: 350px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 12px;
    }
    
    .event-item {
        padding: 5px;
        margin: 3px 0;
        border-left: 3px solid #4ade80;
        padding-left: 10px;
    }
    
    .event-info {
        border-left-color: #4ade80;
    }
    
    .event-warning {
        border-left-color: #fbbf24;
    }
    
    .event-critical {
        border-left-color: #ef4444;
        background-color: rgba(239, 68, 68, 0.1);
    }
    
    .event-timestamp {
        color: #888;
        font-size: 10px;
    }
    
    /* Table styling */
    div[data-testid="stDataFrame"] {
        font-family: 'Courier New', monospace;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1c24;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4ade80;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #22c55e;
    }
    
    /* Panel styling */
    .panel {
        background-color: #1a1c24;
        border: 1px solid #4ade80;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        min-height: 180px;
    }
    
    .panel-title {
        color: #4ade80;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SYNTHETIC DATA GENERATION ---
def generate_synthetic_state() -> dict:
    """Generate synthetic radar/EW state for demo mode."""
    import random
    tick = getattr(generate_synthetic_state, 'tick', 0)
    tick += 1
    generate_synthetic_state.tick = tick
    
    num_tracks = random.randint(2, 8)
    tracks = []
    for i in range(num_tracks):
        tracks.append({
            'id': i + 1,
            'range_m': random.uniform(500, 50000),
            'azimuth_deg': random.uniform(0, 360),
            'radial_velocity_m_s': random.uniform(-500, 500),
            'track_quality': random.uniform(0.6, 0.99),
            'track_confidence_score': random.uniform(0.6, 0.99),
            'threat_class': random.choice(['FRIENDLY', 'NEUTRAL', 'UNKNOWN', 'HOSTILE']),
            'threat_priority': random.randint(0, 10),
            'classification_confidence': random.uniform(0.5, 0.99)
        })
    
    snr_history = []
    for i in range(max(0, tick - 100), tick):
        snr_history.append({
            'frame': i,
            'snr': random.uniform(15, 45) + np.sin(i * 0.1) * 5
        })
    
    threats = [t for t in tracks if t['threat_priority'] >= 5][:5]
    
    return {
        'tick': tick,
        'radar': {
            'status': 'ONLINE',
            'tracks': tracks,
            'detections': len(tracks),
            'threats': threats,
            'snr_history': snr_history[-100:]
        },
        'ew': {
            'status': 'ONLINE',
            'active_jamming': random.random() > 0.7,
            'decision_count': random.randint(10, 500),
            'last_assessment': threats[0] if threats else {
                'threat_class': 'FRIENDLY',
                'threat_priority': 0,
                'classification_confidence': 0.95,
                'engagement_recommendation': 'MONITOR'
            }
        },
        'queues': {
            'ew_to_radar': random.randint(0, 10)
        }
    }

def generate_synthetic_health() -> dict:
    """Generate synthetic health data for demo mode."""
    uptime = getattr(generate_synthetic_health, 'uptime', 0)
    uptime += 1.0
    generate_synthetic_health.uptime = uptime
    
    return {
        'status': 'active',
        'uptime': uptime,
        'cpu_percent': random.uniform(5, 40),
        'memory_mb': random.uniform(100, 500)
    }

def generate_synthetic_events() -> dict:
    """Generate synthetic events for demo mode."""
    events = getattr(generate_synthetic_events, 'events', [])
    
    if len(events) < 50:
        event_types = ['DETECTION', 'TRACK_UPDATE', 'THREAT_ASSESSMENT', 'EW_DECISION', 'SYSTEM_EVENT']
        new_event = {
            'timestamp': datetime.now().isoformat(),
            'type': random.choice(event_types),
            'severity': random.choice(['INFO', 'WARNING', 'CRITICAL']),
            'message': f"SYNTHETIC: {random.choice(['Target acquired', 'Track confirmed', 'EW engagement', 'System online', 'Signal detected'])}"
        }
        events.insert(0, new_event)
        generate_synthetic_events.events = events[:50]
    
    return {'events': events}

def is_api_available() -> bool:
    """Check if API is available."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=API_TIMEOUT)
        return response.status_code == 200
    except:
        return False

# --- API STATE TRACKING ---
_api_available = None
_api_last_check = 0

def check_api_status():
    """Check API status with caching."""
    global _api_available, _api_last_check
    now = time.time()
    if now - _api_last_check > 2:  # Check every 2 seconds
        _api_available = is_api_available()
        _api_last_check = now
    return _api_available

# --- HELPER FUNCTIONS ---
def fetch_state():
    """Fetch system state from API with synthetic fallback."""
    try:
        if check_api_status():
            response = requests.get(f"{API_URL}/state", timeout=API_TIMEOUT)
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return generate_synthetic_state()

def fetch_health():
    """Fetch system health from API with synthetic fallback."""
    try:
        if check_api_status():
            response = requests.get(f"{API_URL}/health", timeout=API_TIMEOUT)
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return generate_synthetic_health()

def fetch_events():
    """Fetch recent events from API with synthetic fallback."""
    try:
        if check_api_status():
            response = requests.get(f"{API_URL}/events", timeout=API_TIMEOUT)
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return generate_synthetic_events()


def get_threat_color(threat_class: str) -> str:
    """Get color class for threat level."""
    if not isinstance(threat_class, str):
        threat_class = str(threat_class) if threat_class else 'UNKNOWN'
    
    threat_map = {
        'FRIENDLY': 'threat-friendly',
        'NEUTRAL': 'threat-neutral',
        'UNKNOWN': 'threat-unknown',
        'HOSTILE': 'threat-hostile'
    }
    return threat_map.get(threat_class.upper(), 'threat-unknown')

def get_priority_badge(priority) -> str:
    """Get priority badge HTML."""
    try:
        priority = int(priority) if priority is not None else 0
    except (ValueError, TypeError):
        priority = 0
    
    if priority >= 7:
        return f'<span class="priority-high">CRITICAL</span>'
    elif priority >= 4:
        return f'<span class="priority-medium">MEDIUM</span>'
    else:
        return f'<span class="priority-low">LOW</span>'

def format_event(event: dict) -> str:
    """Format event for display."""
    if not isinstance(event, dict):
        return ""
        
    severity = str(event.get('severity', 'INFO')).lower()
    severity_class = f"event-{severity}"
    timestamp = event.get('timestamp', '--:--:--')
    message = event.get('message', 'No message')
    event_type = event.get('type', 'EVENT')
    
    return f'<div class="event-item {severity_class}"><span class="event-timestamp">[{timestamp}]</span> <strong>{event_type}</strong>: {message}</div>'

def render_radar_console(state, threats=None):
    """Render the radar console visualization."""
    r_stats = state.get('radar', {})
    tracks = r_stats.get('tracks', [])
    snr_history = r_stats.get('snr_history', [])
    
    # Create a mapping of track_id to threat_class
    threat_map = {}
    if threats:
        for t in threats:
            tid = t.get('id') or t.get('track_id')
            if tid is not None:
                threat_map[str(tid)] = t.get('threat_class', 'UNKNOWN')
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="panel-title">📡 PPI DISPLAY (PLAN POSITION INDICATOR)</div>', unsafe_allow_html=True)
        
        # Prepare data for PPI
        if tracks:
            df = pd.DataFrame(tracks)
            
            # Map threat class to color
            color_map = {
                'FRIENDLY': '#4ade80',  # Green
                'CIVILIAN': '#4ade80',  # Green mapping
                'NEUTRAL': '#fbbf24',   # Yellow
                'UNKNOWN': '#fb923c',   # Orange
                'HOSTILE': '#ef4444'    # Red
            }
            
            # Create Polar Scatter Plot
            fig = go.Figure()
            
            # Add tracks
            for i, row in df.iterrows():
                track_id = row.get('id') or row.get('track_id')
                threat_class = threat_map.get(str(track_id), 'UNKNOWN')
                
                color = color_map.get(threat_class, '#fb923c')
                
                # Safe defaults for formatting
                r_val = row.get('range_m') or 0.0
                az_val = row.get('azimuth_deg') or 0.0
                v_val = row.get('radial_velocity_m_s') or 0.0
                track_id = row.get('id') or row.get('track_id') or 'UNK'
                
                fig.add_trace(go.Scatterpolar(
                    r=[r_val],
                    theta=[az_val],
                    mode='markers',
                    marker=dict(
                        size=12,
                        color=color,
                        line=dict(color='white', width=1)
                    ),
                    name=f"Track {track_id}",
                    hoverinfo='text',
                    text=f"ID: {track_id}<br>R: {r_val:.1f}m<br>Az: {az_val:.1f}°<br>V: {v_val:.1f}m/s"
                ))
            
            # Add EW Jamming Overlay (Mock based on EW status)
            e_stats = state.get('ew', {})
            if e_stats.get('decision_count', 0) > 0:
                 fig.add_trace(go.Scatterpolar(
                    r=[500, 500, 0, 0],
                    theta=[0, 45, 0, 0], # Mock 45 deg sector
                    fill='toself',
                    fillcolor='rgba(239, 68, 68, 0.2)',
                    line=dict(color='rgba(239, 68, 68, 0.5)'),
                    name='Jamming Sector'
                ))
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                polar=dict(
                    radialaxis=dict(showticklabels=True, ticks='', linewidth=1, gridcolor='#333'),
                    angularaxis=dict(showticklabels=True, ticks='', linewidth=1, gridcolor='#333'),
                    bgcolor='#0e1117'
                ),
                margin=dict(l=20, r=20, t=20, b=20),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("Searching for targets...")
            
            # Show empty grid
            fig = go.Figure()
            fig.update_layout(
                template='plotly_dark',
                polar=dict(
                    radialaxis=dict(showticklabels=True, visible=True, range=[0, 1000]),
                    angularaxis=dict(
                        rotation=90, 
                        direction="clockwise",
                        gridcolor='#333'
                    ),
                    bgcolor='#0e1117'
                ),
                margin=dict(l=20, r=20, t=20, b=20),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="panel-title">📉 DETECTION TIMELINE (RANGE-TIME)</div>', unsafe_allow_html=True)
        
        # We need historical track data for this.
        # Currently we only have snr_history and current tracks.
        # Let's use detection_history if available, otherwise mock with snr
        
        det_history = state.get('radar', {}).get('detection_history', [])
        
        if det_history:
             # Process history for Plotly
             # history is list of dicts with 'tracks' list
             plot_data = []
             for frame_data in det_history:
                 frame_idx = frame_data.get('frame', 0)
                 # Note: tracks in history might be simplified or not
                 # Let's assume for now we use the SNR history which is simpler
                 pass
        
        # Fallback/Alternative: Range vs Time scatter of current tracks
        # or better: Signal Strength vs Time (we already have this)
        
        # Let's build a proper formatted snr scatter
        if snr_history:
            df = pd.DataFrame(snr_history)
            if not df.empty and 'frame' in df.columns and 'snr' in df.columns:
                 fig = px.scatter(
                    df, 
                    x='frame', 
                    y='snr',
                    color='snr',
                    color_continuous_scale='Viridis',
                    template='plotly_dark',
                    height=400
                 )
                 fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="Frame",
                    yaxis_title="SNR (dB)"
                 )
                 st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Waiting for history data...")
        else:
            st.info("Initializing timeline...")


# --- MAIN DASHBOARD ---
def main():
    # Title
    st.markdown('<h1 style="text-align: center;">📡 PHOENIX TACTICAL COMMAND</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # --- SYSTEM STATUS PANEL (NEW) ---
    api_status = check_api_status()
    status_container = st.container()
    with status_container:
        col_status1, col_status2, col_status3, col_status4 = st.columns([2, 2, 2, 4])
        
        with col_status1:
            status_icon = "🟢" if api_status else "🟡"
            status_text = "LIVE" if api_status else "DEMO"
            st.markdown(f"""
            <div class="metric-card" style="background: {'rgba(34, 197, 94, 0.1)' if api_status else 'rgba(251, 146, 60, 0.1)'} !important; border-color: {'#22c55e' if api_status else '#fb923c'} !important;">
                <div class="metric-value" style="font-size: 20px; color: {'#22c55e' if api_status else '#fb923c'} !important;">{status_icon} API</div>
                <div class="metric-label">{status_text} MODE</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_status2:
            st.markdown(f"""
            <div class="metric-card" style="background: rgba(34, 197, 94, 0.1) !important; border-color: #22c55e !important;">
                <div class="metric-value" style="font-size: 20px; color: #22c55e !important;">🟢 SIM</div>
                <div class="metric-label">RUNNING</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_status3:
            st.markdown(f"""
            <div class="metric-card" style="background: rgba(34, 197, 94, 0.1) !important; border-color: #22c55e !important;">
                <div class="metric-value" style="font-size: 20px; color: #22c55e !important;">🟢 BRAIN</div>
                <div class="metric-label">ACTIVE</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_status4:
            mode_text = "Connected to http://localhost:5000" if api_status else "Using synthetic demo data - no backend required!"
            st.markdown(f"""
            <div class="panel">
                <strong>System Mode:</strong> {mode_text}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Create tabs
    tab_dashboard, tab_console = st.tabs(["📊 DASHBOARD", "🎯 RADAR CONSOLE"])
    
    with tab_dashboard:
        # Create placeholders
        header_col1, header_col2, header_col3, header_col4 = st.columns(4)
        
        st.markdown("---")
        
        col_left, col_right = st.columns([7, 3])
    
    with col_left:
        st.markdown('<div class="panel-title">📍 ACTIVE RADAR TRACKS</div>', unsafe_allow_html=True)
        tracks_placeholder = st.empty()
        
        st.markdown('<div class="panel-title">📈 SIGNAL STRENGTH HISTORY (SNR)</div>', unsafe_allow_html=True)
        graph_placeholder = st.empty()
        
        st.markdown('<div class="panel-title">⚠️ THREAT ASSESSMENTS</div>', unsafe_allow_html=True)
        threats_placeholder = st.empty()
        
    with col_right:
        st.markdown('<div class="panel-title">⚡ EW STATUS</div>', unsafe_allow_html=True)
        ew_placeholder = st.empty()
        
        st.markdown('<div class="panel-title">📝 LIVE EVENT TICKER</div>', unsafe_allow_html=True)
        events_placeholder = st.empty()
        
        st.markdown('<div class="panel-title">💚 SYSTEM HEALTH</div>', unsafe_allow_html=True)
        health_placeholder = st.empty()

    # --- AUTO REFRESH LOOP ---
    while True:
        state = fetch_state()
        health = fetch_health()
        events = fetch_events()
        
        # --- SAFE GETTERS (Crash prevention) ---
        if state and isinstance(state, dict):
            tick = state.get('tick', 0)
            tick = state.get('tick', 0)
            
            # 1. HEADER METRICS
            with header_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{tick}</div>
                    <div class="metric-label">Simulation Tick</div>
                </div>
                """, unsafe_allow_html=True)
                
            with header_col2:
                r_stats = state.get('radar', {})
                r_status = "ONLINE" if r_stats.get('status') != "OFFLINE" else "OFFLINE"
                track_count = len(r_stats.get('tracks', []))
                status_class = "status-online" if r_status == "ONLINE" else "status-offline"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{track_count}</div>
                    <div class="metric-label">Active Tracks (<span class="{status_class}">{r_status}</span>)</div>
                </div>
                """, unsafe_allow_html=True)

            with header_col3:
                e_stats = state.get('ew', {})
                decisions = e_stats.get('decision_count', 0)
                active = e_stats.get('active_jamming', False)
                ew_status = "ENGAGING" if active else "SCANNING"
                status_class = "status-online" if active else "status-waiting"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{decisions}</div>
                    <div class="metric-label">EW Decisions (<span class="{status_class}">{ew_status}</span>)</div>
                </div>
                """, unsafe_allow_html=True)
                
            with header_col4:
                q_stats = state.get('queues', {})
                ew_q = q_stats.get('ew_to_radar', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{ew_q}</div>
                    <div class="metric-label">Feedback Queue</div>
                </div>
                """, unsafe_allow_html=True)

            # 2. TRACKS TABLE
            tracks = r_stats.get('tracks', [])
            if tracks:
                # Add a display_id column that picks the best ID
                df = pd.DataFrame(tracks)
                if 'id' in df.columns or 'track_id' in df.columns:
                    df['display_id'] = df.apply(lambda r: r.get('id') or r.get('track_id'), axis=1)
                
                cols_to_show = ['display_id', 'range_m', 'azimuth_deg', 'radial_velocity_m_s', 'track_quality', 'track_confidence_score']
                available_cols = [c for c in cols_to_show if c in df.columns]
                
                if available_cols:
                    display_df = df[available_cols].copy()
                    # Rename columns for display
                    rename_dict = {
                        'display_id': 'Track ID',
                        'range_m': 'Range (m)',
                        'azimuth_deg': 'Azimuth (°)',
                        'radial_velocity_m_s': 'Velocity (m/s)',
                        'track_quality': 'Quality',
                        'track_confidence_score': 'Quality'
                    }
                    display_df.rename(columns=rename_dict, inplace=True)
                    
                    # Format numeric columns safely
                    formatted_df = display_df.copy()
                    for col in formatted_df.columns:
                        try:
                            # Only format if column has numeric data
                            if pd.api.types.is_numeric_dtype(formatted_df[col]):
                                if col in ['Range (m)', 'Azimuth (°)', 'Velocity (m/s)']:
                                    formatted_df[col] = formatted_df[col].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
                                elif col == 'Quality':
                                    formatted_df[col] = formatted_df[col].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) else "N/A")
                        except (TypeError, ValueError):
                            # Skip formatting if column can't be converted
                            pass
                    
                    # Display with simple styling (avoid complex styler chains that can fail)
                    try:
                        tracks_placeholder.dataframe(
                            formatted_df,
                            use_container_width=True,
                            height=200
                        )
                    except Exception as e:
                        st.warning(f"✓ Tracks displayed (styling disabled due to: {str(e)[:50]})")
                        tracks_placeholder.dataframe(formatted_df, use_container_width=True)
                else:
                    tracks_placeholder.info("📊 Track data format unavailable")
            else:
                tracks_placeholder.info("🔍 NO ACTIVE TRACKS DETECTED")

            # 2.5 LIVE DETECTION GRAPH (SNR)
            snr_history = r_stats.get('snr_history', [])
            if snr_history:
                snr_df = pd.DataFrame(snr_history)
                # Ensure we have data to plot
                if not snr_df.empty and 'frame' in snr_df.columns and 'snr' in snr_df.columns:
                    # Create Area Chart
                    fig = px.area(
                        snr_df, 
                        x='frame', 
                        y='snr',
                        template='plotly_dark',
                        height=250
                    )
                    
                    # Style the chart
                    fig.update_traces(
                        line_color='#4ade80',
                        fillcolor='rgba(74, 222, 128, 0.2)'
                    )
                    
                    fig.update_layout(
                        margin=dict(l=20, r=20, t=10, b=20),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis_title="Frame",
                        yaxis_title="SNR (dB)",
                        showlegend=False
                    )
                    
                    fig.update_xaxes(showgrid=False)
                    fig.update_yaxes(showgrid=True, gridcolor='#333')
                    
                    graph_placeholder.plotly_chart(fig, use_container_width=True)
                else:
                    graph_placeholder.info("Waiting for signal data...")
            else:
                # If no history yet, show empty chart placeholder or info
                graph_placeholder.info("📡 Initializing Signal History...")

            # 3. THREATS TABLE
            threats = r_stats.get('threats', [])
            if threats:
                threat_data = []
                for t in threats:
                    if isinstance(t, dict):
                        threat_class = t.get('threat_class', 'UNKNOWN')
                        priority = t.get('threat_priority', 0)
                        track_id = t.get('track_id', 0)
                        confidence = t.get('classification_confidence', 0.0)
                        
                        threat_data.append({
                            'Track ID': track_id,
                            'Threat Class': threat_class,
                            'Priority': priority,
                            'Confidence': f"{confidence:.2f}"
                        })
                
                if threat_data:
                    threat_df = pd.DataFrame(threat_data)
                    
                    # Display threat data without complex styling to avoid compatibility issues
                    try:
                        threats_placeholder.dataframe(
                            threat_df,
                            use_container_width=True,
                            height=200
                        )
                    except Exception as e:
                        st.warning(f"✓ Threats displayed (styling disabled due to: {str(e)[:50]})")
                        threats_placeholder.dataframe(threat_df, use_container_width=True)
                else:
                    threats_placeholder.info("📊 Threat data format unavailable")
            else:
                threats_placeholder.info("✅ NO THREATS DETECTED")

            # 4. EW ASSESSMENT
            last_assessment = e_stats.get('last_assessment')
            if last_assessment and isinstance(last_assessment, dict):
                threat_class = last_assessment.get('threat_class', 'UNKNOWN')
                priority = last_assessment.get('threat_priority', 0)
                confidence = last_assessment.get('classification_confidence', 0.0)
                engagement = last_assessment.get('engagement_recommendation', 'MONITOR')
                
                threat_color = get_threat_color(threat_class)
                priority_badge = get_priority_badge(priority)
                
                ew_placeholder.markdown(f"""
                <div class="panel">
                    <p><strong>Threat Class:</strong> <span class="{threat_color}">{threat_class}</span></p>
                    <p><strong>Priority:</strong> {priority_badge} ({priority}/10)</p>
                    <p><strong>Confidence:</strong> {confidence:.2%}</p>
                    <p><strong>Recommendation:</strong> {engagement}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                ew_placeholder.info("⏳ NO EW ASSESSMENT DATA")
                
            # 5. EVENT TICKER
            if events and isinstance(events.get('events'), list):
                event_list = events['events'][::-1] # Newest first
                event_html_items = []
                for event in event_list[:30]:  # Show last 30 events
                    html = format_event(event)
                    if html:
                        event_html_items.append(html)
                
                if event_html_items:
                    event_html = '<div class="event-ticker">' + "".join(event_html_items) + '</div>'
                    events_placeholder.markdown(event_html, unsafe_allow_html=True)
                else:
                    events_placeholder.info("📡 WAITING FOR SYSTEM EVENTS...")
            else:
                events_placeholder.info("📡 NO EVENTS LOGGED")
            
            # 6. SYSTEM HEALTH
            if health and isinstance(health, dict):
                status = health.get('status', 'unknown')
                uptime = health.get('uptime', 0)
                status_class = "status-online" if status == "active" else "status-offline"
                
                health_placeholder.markdown(f"""
                <div class="panel">
                    <p><strong>Status:</strong> <span class="{status_class}">{status.upper()}</span></p>
                    <p><strong>Uptime:</strong> {uptime:.1f}s</p>
                    <p><strong>Last Update:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                health_placeholder.info("⏳ Initializing health data...")

            # 7. UPDATE RADAR CONSOLE
            with tab_console:
                threats = state.get('radar', {}).get('threats', []) if isinstance(state, dict) else []
                render_radar_console(state, threats)
        
        time.sleep(REFRESH_RATE)
        st.rerun()

if __name__ == "__main__":
    main()
