
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURATION ---
API_URL = "http://localhost:5000"
REFRESH_RATE = 1.0  # Seconds

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

# --- HELPER FUNCTIONS ---
def fetch_state():
    """Fetch system state from API."""
    try:
        response = requests.get(f"{API_URL}/state", timeout=0.5)
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

def fetch_health():
    """Fetch system health from API."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=0.5)
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

def fetch_events():
    """Fetch recent events from API."""
    try:
        response = requests.get(f"{API_URL}/events", timeout=0.5)
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

def get_threat_color(threat_class: str) -> str:
    """Get color class for threat level."""
    threat_map = {
        'FRIENDLY': 'threat-friendly',
        'NEUTRAL': 'threat-neutral',
        'UNKNOWN': 'threat-unknown',
        'HOSTILE': 'threat-hostile'
    }
    return threat_map.get(threat_class, 'threat-unknown')

def get_priority_badge(priority: int) -> str:
    """Get priority badge HTML."""
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
    
    return f"""
    <div class="event-item {severity_class}">
        <span class="event-timestamp">[{timestamp}]</span> 
        <strong>{event_type}</strong>: {message}
    </div>
    """

def render_radar_console(state):
    """Render the radar console visualization."""
    r_stats = state.get('radar', {})
    tracks = r_stats.get('tracks', [])
    snr_history = r_stats.get('snr_history', [])
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="panel-title">📡 PPI DISPLAY (PLAN POSITION INDICATOR)</div>', unsafe_allow_html=True)
        
        # Prepare data for PPI
        if tracks:
            df = pd.DataFrame(tracks)
            
            # Map threat class to color
            color_map = {
                'FRIENDLY': '#4ade80',  # Green
                'NEUTRAL': '#fbbf24',   # Yellow
                'UNKNOWN': '#fb923c',   # Orange
                'HOSTILE': '#ef4444'    # Red
            }
            
            # Create Polar Scatter Plot
            fig = go.Figure()
            
            # Add tracks
            for i, row in df.iterrows():
                # Get threat class from track if available, else standard logic
                # For now assume simulation provides class or we default
                threat_class = 'UNKNOWN' 
                # Ideally threat info is merged here, but for now use simple logic or mock
                
                color = color_map.get(threat_class, '#fb923c')
                
                # Safe defaults for formatting
                r_val = row.get('range_m') or 0.0
                az_val = row.get('azimuth_deg') or 0.0
                v_val = row.get('radial_velocity_m_s') or 0.0
                track_id = row.get('track_id', 'UNK')
                
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
        
        if state:
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
                df = pd.DataFrame(tracks)
                cols_to_show = ['track_id', 'range_m', 'azimuth_deg', 'radial_velocity_m_s', 'track_quality']
                available_cols = [c for c in cols_to_show if c in df.columns]
                
                if available_cols:
                    display_df = df[available_cols].copy()
                    display_df.columns = ['Track ID', 'Range (m)', 'Azimuth (°)', 'Velocity (m/s)', 'Quality']
                    
                    tracks_placeholder.dataframe(
                        display_df.style.format({
                            'Range (m)': "{:.1f}",
                            'Azimuth (°)': "{:.1f}",
                            'Velocity (m/s)': "{:.1f}",
                            'Quality': "{:.2f}"
                        }).background_gradient(subset=['Quality'], cmap='Greens'),
                        use_container_width=True,
                        height=200
                    )
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
                    
                    # Apply color styling
                    def highlight_threats(row):
                        threat_class = row['Threat Class']
                        priority = row['Priority']
                        
                        if threat_class == 'HOSTILE' or priority >= 7:
                            return ['background-color: rgba(239, 68, 68, 0.2)'] * len(row)
                        elif threat_class == 'UNKNOWN' or priority >= 4:
                            return ['background-color: rgba(251, 146, 60, 0.2)'] * len(row)
                        elif threat_class == 'NEUTRAL':
                            return ['background-color: rgba(251, 191, 36, 0.2)'] * len(row)
                        else:
                            return ['background-color: rgba(74, 222, 128, 0.1)'] * len(row)
                    
                    threats_placeholder.dataframe(
                        threat_df.style.apply(highlight_threats, axis=1),
                        use_container_width=True,
                        height=200
                    )
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
                event_list = events['events']
                event_html_items = []
                for event in event_list[:20]:  # Show last 20 events
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
            if health:
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
                health_placeholder.warning("⚠️ HEALTH DATA UNAVAILABLE")

            # 7. UPDATE RADAR CONSOLE
            with tab_console:
                render_radar_console(state)

        else:
            st.error("⚠️ API CONNECTION LOST - RECONNECTING...")
        
        time.sleep(REFRESH_RATE)
        st.rerun()

if __name__ == "__main__":
    main()
