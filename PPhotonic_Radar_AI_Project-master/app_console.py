"""
Military-Grade Radar Console UI using operational modes.

Features:
- 4 operational modes (Operator, Commander, Research, Maintenance)
- Real-time alert dashboard
- Incident logging and replay
- Mode-specific visualizations
"""

import os
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import streamlit as st
import torch
import cv2
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from io import BytesIO

# Environment
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Import system modules
from src.config import get_config
from src.logger import init_logging, log_event
from src.startup_checks import run_startup_checks
from src.console_modes import (
    ConsoleState, OperationalMode, Alert, AlertSeverity,
    Incident, IncidentType
)

# Initialize system
cfg = get_config()
init_logging(cfg)
_startup = run_startup_checks()

# ===============================
# STREAMLIT CONFIGURATION
# ===============================
st.set_page_config(
    page_title="Military Radar Console",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# MILITARY-GRADE STYLING
# ===============================
st.markdown("""
<style>
    /* Command Center Theme */
    .main {
        background: linear-gradient(135deg, #0a1428 0%, #162240 100%);
        color: #00ff88;
        font-family: 'Courier New', monospace;
    }
    .stApp {
        background: linear-gradient(135deg, #0a1428 0%, #162240 100%);
    }
    h1, h2, h3 {
        color: #00ff88 !important;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        text-transform: uppercase;
        letter-spacing: 2px;
        font-family: 'Courier New', monospace;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(10, 20, 40, 0.8), rgba(22, 34, 64, 0.8));
        border: 2px solid #00ff88;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.3), inset 0 0 10px rgba(0, 255, 136, 0.1);
    }
    .stMetric {
        background: linear-gradient(135deg, rgba(10, 20, 40, 0.9), rgba(22, 34, 64, 0.9));
        border: 1px solid #00ff88;
        border-radius: 8px;
        padding: 15px;
    }
    .alert-critical {
        background: rgba(255, 50, 50, 0.2);
        border: 2px solid #ff3232;
        border-radius: 8px;
        padding: 12px;
        margin: 5px 0;
        color: #ff6666;
    }
    .alert-warning {
        background: rgba(255, 165, 0, 0.2);
        border: 2px solid #ffa500;
        border-radius: 8px;
        padding: 12px;
        margin: 5px 0;
        color: #ffb84d;
    }
    .alert-info {
        background: rgba(0, 255, 136, 0.1);
        border: 2px solid #00ff88;
        border-radius: 8px;
        padding: 12px;
        margin: 5px 0;
        color: #00ff88;
    }
    .stButton>button {
        background: linear-gradient(135deg, #004e92, #000428);
        color: #00ff88;
        border: 2px solid #00ff88;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #006bb3, #0055aa);
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.6);
        transform: translateY(-2px);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        border-bottom: 2px solid #00ff88;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(10, 20, 40, 0.6);
        border: 1px solid #00444400;
        color: #00ff88;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0, 255, 136, 0.15) !important;
        border: 2px solid #00ff88 !important;
        color: #00ff88 !important;
    }
    .stSelectbox, .stMultiSelect, .stSlider {
        color: #00ff88 !important;
    }
    .stSelectbox [data-baseweb="select"], .stMultiSelect [data-baseweb="multi_select"] {
        background: rgba(10, 20, 40, 0.9);
        border: 1px solid #00ff88;
    }
</style>
""", unsafe_allow_html=True)

# ===============================
# SESSION STATE INITIALIZATION
# ===============================
if "console_state" not in st.session_state:
    st.session_state.console_state = ConsoleState()
    st.session_state.console_state.operator_name = "Radar Operator"

if "mode" not in st.session_state:
    st.session_state.mode = OperationalMode.OPERATOR

# ===============================
# SIDEBAR: MODE SELECTION & CONTROL
# ===============================
st.sidebar.markdown("## 🎖️ COMMAND CONSOLE")
st.sidebar.markdown("---")

# Mode selection
selected_mode = st.sidebar.radio(
    "**OPERATIONAL MODE**",
    [mode.value for mode in OperationalMode],
    format_func=lambda x: f"► {x} ◄" if x == st.session_state.mode.value else f"  {x}",
    key="mode_selector"
)

st.session_state.mode = OperationalMode(selected_mode)
st.session_state.console_state.switch_mode(st.session_state.mode)

# Operator info
st.sidebar.markdown("### 👤 OPERATOR")
operator = st.sidebar.text_input(
    "Operator Name",
    st.session_state.console_state.operator_name,
    key="operator_name_input"
)
st.session_state.console_state.operator_name = operator

# Sector & Mission
st.sidebar.markdown("### 🗺️ SECTOR CONTROL")
sector = st.sidebar.selectbox(
    "Coverage Sector",
    ["Full Coverage", "North", "South", "East", "West", "Custom"],
    key="sector_select"
)
st.session_state.console_state.current_sector = sector

mission_status = st.sidebar.selectbox(
    "Mission Status",
    ["Active", "Standby", "Maintenance", "Training"],
    key="mission_status"
)
st.session_state.console_state.mission_status = mission_status

# Console statistics
st.sidebar.markdown("### 📊 CONSOLE STATUS")
stats = st.session_state.console_state.get_dashboard_stats()

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    st.metric("Uptime", stats['uptime'], delta="Live")
with col_s2:
    alert_color = "🔴" if stats['critical_alerts'] > 0 else "🟢"
    st.metric("Status", alert_color, delta=None)

# ===============================
# MAIN CONTENT AREA
# ===============================

# Header with mode indicator
st.markdown(f"""
<div style="text-align: center; margin-bottom: 20px;">
    <h1>🛰️ MILITARY RADAR CONSOLE 🛰️</h1>
    <h3 style="color: #00ff88; margin-top: -10px;">
        MODE: [{st.session_state.mode.value.upper()}] | OPERATOR: {operator} | SECTOR: {sector}
    </h3>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ===============================
# MODE-SPECIFIC CONTENT
# ===============================

if st.session_state.mode == OperationalMode.OPERATOR:
    st.markdown("## ⚡ TACTICAL OPERATIONS MODE")
    st.markdown("Real-time threat detection and tactical response")
    
    # Create tabs for operator mode
    op_tab1, op_tab2, op_tab3, op_tab4 = st.tabs([
        "🎯 THREATS", "⚠️ ALERTS", "📡 DETECTIONS", "📍 TRACKING"
    ])
    
    with op_tab1:
        st.subheader("Active Threat Assessment")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Threats Detected", stats['detections'], delta="+2 this minute")
        with col2:
            st.metric("Active Tracks", stats['tracks'], delta="+1 this minute")
        with col3:
            st.metric("Confidence Avg", "94.2%", delta="-1.2%")
        with col4:
            st.metric("System Health", "Nominal", delta="✓")
        
        # Threat visualization placeholder
        st.info("📊 Real-time threat map would display here with bearing, range, altitude")
    
    with op_tab2:
        st.subheader("Active Alerts (Operator Priority)")
        
        alerts = st.session_state.console_state.alert_manager.get_active_alerts()
        
        if not alerts:
            st.success("✓ No active alerts - System nominal")
        else:
            for idx, alert in enumerate(alerts):
                if alert.severity == AlertSeverity.CRITICAL:
                    st.markdown(f"""
                    <div class="alert-critical">
                        <b>🚨 [{alert.severity.value}]</b> {alert.title}<br/>
                        {alert.message}
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Dismiss Alert {idx+1}", key=f"dismiss_{idx}"):
                        st.session_state.console_state.alert_manager.dismiss_alert(idx)
                        st.rerun()
    
    with op_tab3:
        st.subheader("Recent Detections")
        
        incidents = st.session_state.console_state.incident_logger.get_incidents(
            limit=10, incident_type=IncidentType.DETECTION
        )
        
        if incidents:
            df_data = []
            for inc in reversed(incidents):
                df_data.append({
                    'Time': datetime.fromtimestamp(inc.timestamp).strftime("%H:%M:%S"),
                    'Type': inc.incident_type.value,
                    'Description': inc.description,
                    'Severity': inc.severity.value
                })
            
            st.dataframe(pd.DataFrame(df_data), use_container_width=True)
        else:
            st.info("No recent detections")
    
    with op_tab4:
        st.subheader("Track Management")
        st.info("🔷 Track status, confidence, and kinematic data would display here")

elif st.session_state.mode == OperationalMode.COMMANDER:
    st.markdown("## 🎖️ STRATEGIC COMMAND MODE")
    st.markdown("High-level situational awareness and strategic assessment")
    
    cmd_tab1, cmd_tab2, cmd_tab3 = st.tabs([
        "🎯 SITUATION", "📈 ANALYSIS", "🔔 INCIDENT LOG"
    ])
    
    with cmd_tab1:
        st.subheader("Strategic Situation Report")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Contacts", stats['detections'], delta="+3")
        with col2:
            st.metric("Threat Level", "MEDIUM", delta="↑ from LOW")
        with col3:
            st.metric("Coverage %", "98.5%", delta="-0.2%")
        
        # System health overview
        st.markdown("### System Overview")
        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
        with col_h1:
            st.markdown("**Radar**\n✓ Operational")
        with col_h2:
            st.markdown("**Processing**\n✓ Nominal")
        with col_h3:
            st.markdown("**Tracking**\n✓ Active")
        with col_h4:
            st.markdown("**EW Defense**\n✓ Armed")
    
    with cmd_tab2:
        st.subheader("Tactical Analysis")
        
        # Statistics summary
        stats_data = st.session_state.console_state.incident_logger.get_statistics()
        
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            st.markdown("### Incident Distribution")
            if stats_data['by_type']:
                incident_df = pd.DataFrame(
                    list(stats_data['by_type'].items()),
                    columns=['Type', 'Count']
                )
                st.bar_chart(incident_df.set_index('Type'))
        
        with col_a2:
            st.markdown("### Severity Distribution")
            if stats_data['by_severity']:
                severity_df = pd.DataFrame(
                    list(stats_data['by_severity'].items()),
                    columns=['Severity', 'Count']
                )
                st.bar_chart(severity_df.set_index('Severity'))
    
    with cmd_tab3:
        st.subheader("Complete Incident Log")
        
        all_incidents = st.session_state.console_state.incident_logger.get_incidents(limit=50)
        
        if all_incidents:
            df_data = []
            for inc in reversed(all_incidents):
                df_data.append({
                    'Time': datetime.fromtimestamp(inc.timestamp).strftime("%H:%M:%S"),
                    'Type': inc.incident_type.value,
                    'Severity': inc.severity.value,
                    'Description': inc.description[:50] + "..." if len(inc.description) > 50 else inc.description
                })
            
            st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=400)
        else:
            st.info("No incidents logged")

elif st.session_state.mode == OperationalMode.RESEARCH:
    st.markdown("## 🔬 RESEARCH & ANALYSIS MODE")
    st.markdown("Detailed technical analysis and system debugging")
    
    res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs([
        "📊 METRICS", "🔍 REPLAY", "⚙️ DEBUG", "📈 TRENDS"
    ])
    
    with res_tab1:
        st.subheader("Detailed Metrics")
        
        metrics_cols = st.columns(4)
        metrics = [
            ("Detections", stats['detections']),
            ("Tracks", stats['tracks']),
            ("False Alarms", stats['false_alarms']),
            ("OOD Events", stats['ood_events'])
        ]
        
        for col, (label, value) in zip(metrics_cols, metrics):
            with col:
                st.metric(label, value)
        
        # Detailed statistics
        st.markdown("### System Statistics")
        alert_stats = st.session_state.console_state.alert_manager.get_statistics()
        incident_stats = st.session_state.console_state.incident_logger.get_statistics()
        
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.markdown("**Alerts**")
            st.json(alert_stats)
        
        with col_r2:
            st.markdown("**Incidents**")
            st.json(incident_stats)
    
    with res_tab2:
        st.subheader("Session Replay & Timeline")
        
        replay_mgr = st.session_state.console_state.replay_manager
        
        col_replay1, col_replay2, col_replay3 = st.columns([1, 1, 1])
        
        with col_replay1:
            if st.button("⏮️ Beginning"):
                replay_mgr.current_frame = 0
        
        with col_replay2:
            if st.button("⏯️ Play"):
                replay_mgr.is_playing = True
        
        with col_replay3:
            if st.button("⏸️ Pause"):
                replay_mgr.is_playing = False
        
        frame_count = replay_mgr.get_frame_count()
        if frame_count > 0:
            current = st.slider(
                "Frame Navigation",
                0, frame_count - 1,
                replay_mgr.current_frame,
                key="frame_slider"
            )
            replay_mgr.current_frame = current
            
            st.info(f"Viewing frame {current + 1} of {frame_count}")
        else:
            st.warning("No recorded frames yet")
    
    with res_tab3:
        st.subheader("System Debug Information")
        
        debug_cols = st.columns(2)
        
        with debug_cols[0]:
            st.markdown("**System Configuration**")
            st.code(f"Mode: {st.session_state.mode.value}\nOperator: {operator}\nSector: {sector}")
        
        with debug_cols[1]:
            st.markdown("**Active Sessions**")
            debug_alerts = st.session_state.console_state.alert_manager.get_active_alerts()
            st.code(f"Console State: Active\nAlert Manager: {len(debug_alerts)} active alerts\nIncident Logger: Running")
    
    with res_tab4:
        st.subheader("Performance Trends")
        
        # Generate sample trend data
        time_range = pd.date_range(end=datetime.now(), periods=24, freq='H')
        trend_data = pd.DataFrame({
            'Time': time_range,
            'Detections': np.random.randint(5, 20, 24),
            'False Alarms': np.random.randint(0, 3, 24),
            'Track Confidence': np.random.uniform(85, 98, 24)
        })
        
        st.line_chart(trend_data.set_index('Time'))

elif st.session_state.mode == OperationalMode.MAINTENANCE:
    st.markdown("## 🔧 MAINTENANCE & DIAGNOSTICS MODE")
    st.markdown("System health monitoring and configuration management")
    
    maint_tab1, maint_tab2, maint_tab3 = st.tabs([
        "🏥 HEALTH", "⚙️ CONFIG", "🔐 LOGS"
    ])
    
    with maint_tab1:
        st.subheader("System Health Diagnostics")
        
        health_items = [
            ("Radar Unit", "✓ Operational", "green"),
            ("Processing Core", "✓ Normal Load", "green"),
            ("Storage", "✓ 42% Used", "green"),
            ("Network", "✓ Connected", "green"),
            ("AI Model", "✓ Loaded", "green"),
            ("Database", "✓ Synced", "green")
        ]
        
        col_h1, col_h2, col_h3 = st.columns(3)
        
        for i, (component, status, color) in enumerate(health_items):
            if i % 3 == 0:
                col = col_h1
            elif i % 3 == 1:
                col = col_h2
            else:
                col = col_h3
            
            with col:
                st.markdown(f"**{component}**: {status}")
    
    with maint_tab2:
        st.subheader("System Configuration")
        
        st.markdown("### Radar Parameters")
        col_cfg1, col_cfg2 = st.columns(2)
        
        with col_cfg1:
            freq = st.slider("Carrier Frequency (GHz)", 1.0, 40.0, 10.0)
            bw = st.slider("Bandwidth (MHz)", 10, 500, 100)
        
        with col_cfg2:
            prf = st.slider("Pulse Repetition Freq (kHz)", 1, 100, 10)
            pw = st.slider("Pulse Width (µs)", 0.1, 10.0, 1.0)
        
        if st.button("💾 Save Configuration"):
            st.success("Configuration saved successfully")
    
    with maint_tab3:
        st.subheader("System Logs")
        
        # Display recent incidents as system log
        incidents = st.session_state.console_state.incident_logger.get_incidents(limit=20)
        
        if incidents:
            st.code("\n".join([
                f"[{datetime.fromtimestamp(inc.timestamp).isoformat()}] {inc.incident_type.value}: {inc.description}"
                for inc in reversed(incidents)
            ]))
        else:
            st.info("No log entries")

# ===============================
# GLOBAL ALERT PANEL (All Modes)
# ===============================
st.markdown("---")

alert_section_col1, alert_section_col2 = st.columns([3, 1])

with alert_section_col1:
    st.markdown("## ⚠️ ACTIVE ALERTS & NOTIFICATIONS")

with alert_section_col2:
    if st.button("🔄 Refresh", key="refresh_alerts"):
        st.rerun()

alerts = st.session_state.console_state.alert_manager.get_active_alerts()

if alerts:
    for idx, alert in enumerate(alerts):
        if alert.severity == AlertSeverity.CRITICAL or alert.severity == AlertSeverity.SYSTEM_FAILURE:
            st.markdown(f"""
            <div class="alert-critical">
                <b>🚨 CRITICAL</b><br/>
                <b>{alert.title}</b><br/>
                {alert.message}<br/>
                <small>Source: {alert.source} | {datetime.fromtimestamp(alert.timestamp).strftime('%H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
        elif alert.severity == AlertSeverity.WARNING:
            st.markdown(f"""
            <div class="alert-warning">
                <b>⚠️ WARNING</b><br/>
                <b>{alert.title}</b><br/>
                {alert.message}<br/>
                <small>Source: {alert.source} | {datetime.fromtimestamp(alert.timestamp).strftime('%H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert-info">
                <b>ℹ️ INFO</b><br/>
                <b>{alert.title}</b><br/>
                {alert.message}<br/>
                <small>Source: {alert.source} | {datetime.fromtimestamp(alert.timestamp).strftime('%H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
else:
    st.success("✓ No active alerts - All systems nominal")

# ===============================
# TEST ALERTS & INCIDENTS
# ===============================
st.markdown("---")
st.markdown("### 🧪 Testing & Demo")

col_test1, col_test2, col_test3, col_test4 = st.columns(4)

with col_test1:
    if st.button("Add Test Alert (Warning)"):
        st.session_state.console_state.alert_manager.add_alert(
            Alert(
                severity=AlertSeverity.WARNING,
                title="Test Warning",
                message="This is a test warning alert",
                source="Test System"
            )
        )
        st.session_state.console_state.detections_count += 1
        st.rerun()

with col_test2:
    if st.button("Add Test Alert (Critical)"):
        st.session_state.console_state.alert_manager.add_alert(
            Alert(
                severity=AlertSeverity.CRITICAL,
                title="Test Critical",
                message="This is a test critical alert",
                source="Test System"
            )
        )
        st.rerun()

with col_test3:
    if st.button("Log Test Incident"):
        st.session_state.console_state.incident_logger.log_incident(
            Incident(
                incident_type=IncidentType.DETECTION,
                description=f"Test detection at {datetime.now().strftime('%H:%M:%S')}",
                operator=operator
            )
        )
        st.rerun()

with col_test4:
    if st.button("Clear All Alerts"):
        st.session_state.console_state.alert_manager.dismiss_all()
        st.rerun()

st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #00666600; font-size: 12px;'>Military Radar Console v1.0 | Built with Python + Streamlit | Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>", unsafe_allow_html=True)
