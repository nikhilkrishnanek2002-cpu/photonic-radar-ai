#!/usr/bin/env python3
"""
PHOENIX-RADAR Deployment Guide & Quick Start
==============================================

This guide shows how to properly deploy and run the PHOENIX-RADAR system
using the new production-grade main.py entry point.
"""

# =============================================================================
# SECTION 1: INSTALLATION & SETUP
# =============================================================================

"""
STEP 1: Clone Repository
────────────────────────

    git clone https://github.com/nikhilkrishnanek2002-cpu/photonic-radar-ai.git
    cd photonic-radar-ai


STEP 2: Create Virtual Environment
──────────────────────────────────

    # Linux / macOS
    python3 -m venv .venv
    source .venv/bin/activate
    
    # Windows
    python -m venv .venv
    .venv\Scripts\activate


STEP 3: Install Dependencies
─────────────────────────────

    pip install --upgrade pip setuptools
    pip install -r photonic-radar-ai/requirements.txt
    
    # For GPU support (optional)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118


STEP 4: Verify Installation
────────────────────────────

    python3 main.py --help
    
    Expected output:
        usage: main.py [-h] [--debug] [--ui] [--api-only] [--headless]
        PHOENIX-RADAR AI Defense Platform
        ...
"""

# =============================================================================
# SECTION 2: QUICK START EXAMPLES
# =============================================================================

"""
EXAMPLE 1: Headless Radar + API Server
──────────────────────────────────────

Start the platform in headless mode (no dashboard).
API server runs on http://localhost:5000.

    $ python3 main.py
    
    Output:
        ================================================================================
         PHOENIX-RADAR: COGNITIVE PHOTONIC RADAR DEFENSE SYSTEM
         Sensor → Intelligence → EW → Effect
        ================================================================================
        
        System: Linux-5.15.0-1033-aws
        Python: 3.10.6
        Project: /home/user/photonic-radar-ai
        
        ========================================================================
        PHASE 1: CONFIGURATION & LOGGING
        ========================================================================
        [CONFIG] ✓ Configuration loaded
        [CONFIG] ✓ Logging initialized
        
        [EVENT BUS] ✓ Event bus ready
        [TACTICAL] ✓ Tactical state initialized
        [RADAR] ✓ Radar online (10.0 Hz, 3 targets)
        [EW] ✓ EW engine online
        [API] ✓ API server started (http://localhost:5000)
        
        ========================================================================
        ✓ SYSTEM READY
        ========================================================================
        
        API Server: http://localhost:5000
          - GET /state     → Full system state
          - GET /health    → Health status
          - GET /events    → Event log
        
        Radar: Simulation running at 10 Hz
        EW Engine: Cognitive intelligence pipeline active
        Press Ctrl+C to shutdown gracefully...


EXAMPLE 2: With Streamlit Dashboard
────────────────────────────────────

Start with interactive tactical visualization dashboard.
API server runs on http://localhost:5000.
Dashboard runs on http://localhost:8501.

    $ python3 main.py --ui
    
    Browser should auto-open to http://localhost:8501.
    
    Displays:
    - PPI (Plan Position Indicator) radar return
    - Detected targets and tracks
    - Threat assessment and classification
    - EW decision history
    - Real-time event ticker


EXAMPLE 3: Debug Mode with Dashboard
─────────────────────────────────────

Run with verbose logging for troubleshooting.

    $ python3 main.py --ui --debug
    
    Output includes:
    - DEBUG-level messages from all modules
    - Frame-by-frame radar tick logs
    - Event bus traffic details
    - Timestamps for performance analysis


EXAMPLE 4: API Server Only
──────────────────────────

Run only the API server (no radar simulation).
Useful for testing the REST API without running the full system.

    $ python3 main.py --api-only
    
    Starts:
    - REST API server on http://localhost:5000
    - No radar simulation
    - No EW processing
    - Useful for: Testing, API development, CI/CD pipelines


EXAMPLE 5: Headless Dashboard (Server Mode)
───────────────────────────────────────────

Run dashboard without auto-opening browser.
Useful for SSH/remote deployments.

    $ python3 main.py --ui --headless
    
    Starts:
    - Radar simulation
    - EW engine
    - API server (:5000)
    - Streamlit dashboard (:8501, no browser open)
    
    Connect manually:
    - SSH tunnel: ssh -L 8501:localhost:8501 user@server
    - Browser: http://localhost:8501
"""

# =============================================================================
# SECTION 3: PRODUCTION DEPLOYMENT
# =============================================================================

"""
PRODUCTION DEPLOYMENT ON LINUX SERVER
──────────────────────────────────────

1. Install systemd service
───────────────────────────

Create /etc/systemd/system/phoenix-radar.service:

    [Unit]
    Description=PHOENIX-RADAR Defense Platform
    After=network.target
    
    [Service]
    Type=simple
    User=phoenix
    WorkingDirectory=/opt/phoenix-radar
    ExecStart=/opt/phoenix-radar/.venv/bin/python3 main.py --headless
    Restart=always
    RestartSec=10
    StandardOutput=journal
    StandardError=journal
    
    [Install]
    WantedBy=multi-user.target


2. Start the service
────────────────────

    sudo systemctl enable phoenix-radar
    sudo systemctl start phoenix-radar
    sudo systemctl status phoenix-radar


3. View logs
────────────

    # Real-time logs
    sudo journalctl -u phoenix-radar -f
    
    # Last 100 lines
    sudo journalctl -u phoenix-radar -n 100
    
    # Log file
    cat /opt/phoenix-radar/photonic-radar-ai/runtime/logs/phoenix_radar.log


4. Restart the service
──────────────────────

    sudo systemctl restart phoenix-radar


5. Stop the service
────────────────────

    sudo systemctl stop phoenix-radar


DOCKER DEPLOYMENT
─────────────────

Create Dockerfile:

    FROM python:3.10-slim
    
    WORKDIR /app
    COPY . .
    
    RUN pip install --no-cache-dir -r photonic-radar-ai/requirements.txt
    
    EXPOSE 5000 8501
    
    CMD ["python3", "main.py", "--headless"]


Build and run:

    docker build -t phoenix-radar:latest .
    docker run -d -p 5000:5000 -p 8501:8501 phoenix-radar:latest


KUBERNETES DEPLOYMENT
─────────────────────

Create deployment.yaml:

    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: phoenix-radar
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: phoenix-radar
      template:
        metadata:
          labels:
            app: phoenix-radar
        spec:
          containers:
          - name: phoenix-radar
            image: phoenix-radar:latest
            ports:
            - containerPort: 5000
              name: api
            - containerPort: 8501
              name: dashboard
            env:
            - name: PYTHONUNBUFFERED
              value: "1"
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: phoenix-radar-service
    spec:
      selector:
        app: phoenix-radar
      ports:
      - port: 5000
        name: api
      - port: 8501
        name: dashboard
      type: LoadBalancer


Deploy:

    kubectl apply -f deployment.yaml
    kubectl get pods -l app=phoenix-radar
    kubectl logs -f deployment/phoenix-radar
"""

# =============================================================================
# SECTION 4: MONITORING & HEALTH CHECKS
# =============================================================================

"""
HEALTH CHECK ENDPOINT
─────────────────────

    curl http://localhost:5000/health
    
    Response (OK):
    {
        "status": "active",
        "shutdown_requested": false,
        "uptime": 123.45
    }
    
    Response (Error):
    {
        "status": "stopped",
        "error": "No state available"
    }


SYSTEM STATE ENDPOINT
─────────────────────

    curl http://localhost:5000/state | jq
    
    Returns:
    {
        "radar": {
            "detections": [...],
            "detection_history": [...],
            "snr_history": [...],
            "tracks": [...],
            "threats": [...]
        },
        "ew": {
            "active_jamming": "ACTIVE|INACTIVE",
            "decision": "MONITOR|TRACK|ENGAGE",
            "confidence": 0.95,
            "threat_level": 7,
            "threat_class": "HOSTILE"
        },
        "system": {
            "tick": 1234,
            "health": "OK",
            "uptime": 12.34
        }
    }


EVENTS ENDPOINT
───────────────

    curl http://localhost:5000/events | jq
    
    Returns recent system events:
    {
        "events": [
            {
                "timestamp": "14:32:15.123",
                "type": "TRACK_DETECTION",
                "severity": "info",
                "message": "Track 1 entered radar field",
                "data": {"track_id": "1"}
            },
            ...
        ],
        "count": 42
    }


MONITORING SCRIPT (cron job)
─────────────────────────────

Create /opt/phoenix-radar/monitor.sh:

    #!/bin/bash
    
    API_URL="http://localhost:5000"
    LOG_FILE="/opt/phoenix-radar/monitor.log"
    
    # Check health
    HEALTH=$(curl -s $API_URL/health)
    STATUS=$(echo $HEALTH | jq -r .status)
    
    if [ "$STATUS" != "active" ]; then
        echo "$(date): ERROR - System not active. Status: $STATUS" | tee -a $LOG_FILE
        
        # Restart service
        systemctl restart phoenix-radar
        echo "$(date): Restarted phoenix-radar service" | tee -a $LOG_FILE
    else
        UPTIME=$(echo $HEALTH | jq -r .uptime)
        echo "$(date): OK - System active, uptime: ${UPTIME}s" | tee -a $LOG_FILE
    fi


Add to crontab:

    */5 * * * * /opt/phoenix-radar/monitor.sh
    
    (Runs every 5 minutes)
"""

# =============================================================================
# SECTION 5: TROUBLESHOOTING
# =============================================================================

"""
TROUBLESHOOTING GUIDE
─────────────────────

Issue: "Event bus initialization failed"
───────────────────────────────────────

    Symptoms:
    [EVENT BUS] ✗ Event bus initialization failed
    ✗ SYSTEM ABORT: Event bus initialization failed
    
    Cause: defense_core module not found or import error
    
    Solution:
    1. Check defense_core exists:
       python3 -c "from defense_core import get_defense_bus; print('OK')"
    
    2. Check Python path:
       python3 main.py --debug | grep -i "path"
    
    3. Verify installation:
       pip list | grep -i defense


Issue: "Radar initialization failed"
────────────────────────────────────

    Symptoms:
    [RADAR] ✗ Radar initialization failed
    
    Cause: simulation_engine module missing or physics error
    
    Solution:
    1. Check simulation engine:
       python3 -c "from simulation_engine.orchestrator import SimulationOrchestrator; print('OK')"
    
    2. Check dependencies:
       pip install scipy numpy torch


Issue: "API Server failed to start"
───────────────────────────────────

    Symptoms:
    [API] ✗ Failed to start API server: ...
    
    Cause: Port 5000 already in use or uvicorn not installed
    
    Solution:
    1. Check port availability:
       lsof -i :5000
    
    2. Kill process using port:
       kill -9 $(lsof -t -i:5000)
    
    3. Install uvicorn:
       pip install uvicorn flask


Issue: "Dashboard failed to start"
──────────────────────────────────

    Symptoms:
    [DASHBOARD] ✗ Failed to start dashboard: ...
    
    Cause: Port 8501 in use or streamlit not installed
    
    Solution:
    1. Check port:
       lsof -i :8501
    
    2. Install streamlit:
       pip install streamlit
    
    3. Use --headless flag:
       python3 main.py --ui --headless


Issue: "System runs but no detections"
──────────────────────────────────────

    Symptoms:
    System starts OK, but radar shows 0 detections
    
    Cause: SNR too low or targets too far away
    
    Solution:
    1. Check radar telemetry:
       curl http://localhost:5000/state | jq .radar.snr_history
    
    2. Adjust scenario targets in main.py:
       - Move targets closer (reduce range)
       - Increase target RCS value
       - Increase radar power
    
    3. Check event bus traffic:
       python3 main.py --debug | grep -i "detection"


Issue: "High CPU usage"
───────────────────────

    Symptoms:
    CPU utilization at 100%
    
    Cause: Frame rate too high or simulation expensive
    
    Solution:
    1. Reduce frame rate in main.py:
       Change: SimulationClock(hz=10.0)
       To:     SimulationClock(hz=5.0)
    
    2. Profile execution:
       python3 main.py --debug 2>&1 | tail -100


Issue: "Memory grows unbounded"
───────────────────────────────

    Symptoms:
    Memory usage grows over time, eventually OOM
    
    Cause: Detection/track history not pruned
    
    Solution:
    1. Check history sizes in main.py:
       radar.telemetry_history = deque(maxlen=200)
       radar.detection_history = deque(maxlen=500)
    
    2. Monitor memory:
       ps aux | grep main.py
       watch -n 1 'ps aux | grep main.py'
"""

# =============================================================================
# SECTION 6: PERFORMANCE TUNING
# =============================================================================

"""
PERFORMANCE OPTIMIZATION GUIDELINES
────────────────────────────────────

1. Frame Rate Tuning
────────────────────

    Default: 10 Hz (100ms per frame)
    Budget: ~55ms used, 45ms headroom
    
    For lower latency:
        SimulationClock(hz=20.0)  # 50ms per frame
        (Requires optimization of radar.tick() under 25ms)
    
    For lower CPU:
        SimulationClock(hz=5.0)   # 200ms per frame
        (Reduces update frequency)


2. Detection History Tuning
──────────────────────────

    Default: 500 detections in history
    
    To reduce memory:
        detection_history = deque(maxlen=100)  # Smaller window
    
    To increase history depth:
        detection_history = deque(maxlen=1000) # Larger window


3. EW Pipeline Optimization
───────────────────────────

    Disable if not needed:
        Edit initialize_ew_subsystem() in main.py
        Return False early to skip EW
    
    Result: ~15ms saved per frame


4. API Server Optimization
───────────────────────────

    Use uvicorn with multiple workers:
        uvicorn api.server:app --workers 4 --host 0.0.0.0 --port 5000
    
    Enable caching in dashboard:
        @st.cache_data
        def fetch_state():
            return requests.get(...).json()


5. Logging Optimization
───────────────────────

    Reduce log level in production:
        python3 main.py  # INFO level (less logging)
    
    Avoid debug mode in production:
        python3 main.py --debug  # DO NOT use (verbose)
"""

# =============================================================================
# SECTION 7: INTEGRATION WITH EXISTING SYSTEMS
# =============================================================================

"""
MQTT INTEGRATION
────────────────

Subscribe radar detections to MQTT broker:

    import paho.mqtt.client as mqtt
    
    client = mqtt.Client()
    client.connect("mqtt-broker", 1883)
    
    # In main loop:
    def publish_to_mqtt(state):
        msg = json.dumps(state)
        client.publish("phoenix-radar/state", msg)


DATABASE INTEGRATION
────────────────────

Log detections to PostgreSQL:

    import psycopg2
    
    conn = psycopg2.connect("dbname=radar user=postgres")
    cur = conn.cursor()
    
    # In main loop:
    def log_to_db(detection):
        cur.execute(
            "INSERT INTO detections (timestamp, track_id, range, azimuth) "
            "VALUES (%s, %s, %s, %s)",
            (time.time(), detection['track_id'], detection['range'], detection['az'])
        )
        conn.commit()


HARDWARE INTEGRATION
────────────────────

Use real radar hardware instead of simulation:

    # Replace radar.tick() with hardware poll:
    def hardware_tick():
        raw_data = hardware_interface.read_frame()
        detections = process_hardware_data(raw_data)
        return detections
    
    # Hook into main loop
    radar_result = hardware_tick()
"""

# =============================================================================
# SECTION 8: BEST PRACTICES
# =============================================================================

"""
PRODUCTION DEPLOYMENT CHECKLIST
────────────────────────────────

✓ Pre-Deployment
  [ ] Update requirements.txt with pinned versions
  [ ] Test on target OS/Python version
  [ ] Verify all imports: python3 main.py --api-only
  [ ] Run system for 1 hour to check stability
  [ ] Configure monitoring/alerting

✓ Deployment
  [ ] Use systemd service (Linux) or equivalent
  [ ] Enable log rotation (daily, 7-day retention)
  [ ] Set up health checks (cron job or monitoring tool)
  [ ] Document access credentials/API keys
  [ ] Configure firewall rules

✓ Post-Deployment
  [ ] Verify system boots after reboot
  [ ] Test API endpoints manually
  [ ] Set up monitoring dashboard
  [ ] Create runbooks for common failures
  [ ] Document recovery procedures

✓ Ongoing
  [ ] Monitor system metrics (CPU, memory, disk)
  [ ] Review logs weekly
  [ ] Update dependencies monthly
  [ ] Plan major version upgrades


LOGGING BEST PRACTICES
──────────────────────

1. Use structured logging in production:
   - JSON format for easy log aggregation
   - Add trace IDs for request correlation
   - Include timestamps in all logs


2. Log rotation:
   - daily rotation with 7-day retention
   - Compress rotated logs after 1 day
   - Monitor disk usage


3. External log aggregation:
   - Use ELK stack for centralized logging
   - Set up alerts for ERROR/CRITICAL
   - Create dashboards for monitoring


4. Audit logging:
   - Log all API calls (method, path, status)
   - Log system state transitions
   - Retain for compliance (90+ days)
"""

# =============================================================================
# END OF DEPLOYMENT GUIDE
# =============================================================================

if __name__ == '__main__':
    print(__doc__)
