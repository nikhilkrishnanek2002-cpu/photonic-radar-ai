#!/bin/bash
# DASHBOARD_TEST.sh - Quick test guide for PHOENIX Tactical Dashboard

echo "════════════════════════════════════════════════════════════════"
echo "  PHOENIX TACTICAL COMMAND - DASHBOARD TEST GUIDE"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Show current Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python Version: $PYTHON_VERSION"
echo ""

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import streamlit; import requests; import plotly; print('✅ All dependencies available')" 2>/dev/null || {
    echo "⚠️  Missing dependencies. Installing..."
    pip install streamlit requests plotly pandas numpy
}
echo ""

# Get workspace path
WORKSPACE="/home/nikhil/PycharmProjects/photonic-radar-ai"
cd "$WORKSPACE" || exit 1

echo "Workspace: $WORKSPACE"
echo "Dashboard Path: photonic-radar-ai/ui/dashboard.py"
echo ""

# Validate syntax
echo "════════════════════════════════════════════════════════════════"
echo "  RUNNING SYNTAX CHECK"
echo "════════════════════════════════════════════════════════════════"
python3 -m py_compile photonic-radar-ai/ui/dashboard.py
if [ $? -eq 0 ]; then
    echo "✅ Syntax check PASSED"
else
    echo "❌ Syntax check FAILED"
    exit 1
fi
echo ""

# Test Mode 1: Demo Mode (Standalone)
echo "════════════════════════════════════════════════════════════════"
echo "  TEST MODE 1: DEMO (Standalone, No Backend)"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Command: streamlit run photonic-radar-ai/ui/dashboard.py"
echo ""
echo "Expected results:"
echo "  • Dashboard loads successfully"
echo "  • Status panel shows: 🟡 DEMO MODE"
echo "  • Radar tracks appear immediately"
echo "  • Signal strength history displays"
echo "  • Threat assessments visible"
echo "  • Event ticker shows synthetic events"
echo "  • System health shows active"
echo ""
echo "This test requires human interaction:"
echo "  1. Open another terminal"
echo "  2. Run: streamlit run photonic-radar-ai/ui/dashboard.py"
echo "  3. Dashboard opens at http://localhost:8501"
echo "  4. Verify all elements render without errors"
echo "  5. Check that data updates every second"
echo "  6. Verify no crashes on rapid refresh"
echo ""

# Test Mode 2: Live Mode (with Backend)
echo "════════════════════════════════════════════════════════════════"
echo "  TEST MODE 2: LIVE (With Backend API)"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Setup steps:"
echo "  1. Terminal A: python3 main.py"
echo "     (starts backend API on localhost:5000)"
echo ""
echo "  2. Terminal B: streamlit run photonic-radar-ai/ui/dashboard.py"
echo "     (starts dashboard on localhost:8501)"
echo ""
echo "Expected results:"
echo "  • Dashboard loads successfully"
echo "  • Status panel shows: 🟢 LIVE MODE"
echo "  • API data flows from backend"
echo "  • Radar tracks match backend state"
echo "  • Error logs show no connection issues"
echo ""

# Test Mode 3: API Failure Recovery
echo "════════════════════════════════════════════════════════════════"
echo "  TEST MODE 3: API FAILURE RECOVERY (Manual)"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Steps:"
echo "  1. Start system with: python3 main.py"
echo "  2. Start dashboard with: streamlit run photonic-radar-ai/ui/dashboard.py"
echo "  3. Verify it shows 🟢 LIVE MODE"
echo "  4. Kill the main.py process (Ctrl+C)"
echo "  5. Dashboard should detect failure within 2 seconds"
echo "  6. Status should change to 🟡 DEMO MODE"
echo "  7. Data stream continues with synthetic data"
echo "  8. Verify no crashes or errors"
echo ""

# Quick validation
echo "════════════════════════════════════════════════════════════════"
echo "  QUICK VALIDATION"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check file exists
if [ -f "photonic-radar-ai/ui/dashboard.py" ]; then
    echo "✅ Dashboard file exists"
else
    echo "❌ Dashboard file not found"
    exit 1
fi

# Check main.py exists
if [ -f "main.py" ]; then
    echo "✅ Main entry point exists"
else
    echo "❌ Main entry point not found"
fi

# Check requirements
if [ -f "requirements.txt" ]; then
    echo "✅ Requirements file exists"
    echo ""
    echo "Required packages in requirements.txt:"
    grep -E "streamlit|requests|plotly|pandas|numpy" requirements.txt || echo "  (checking...)"
else
    echo "⚠️  Requirements file not found"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  NEXT STEPS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Option A - Demo Mode (fastest, no backend needed):"
echo "  $ streamlit run photonic-radar-ai/ui/dashboard.py"
echo ""
echo "Option B - Live Mode (requires backend):"
echo "  Terminal 1: $ python3 main.py"
echo "  Terminal 2: $ streamlit run photonic-radar-ai/ui/dashboard.py"
echo ""
echo "════════════════════════════════════════════════════════════════"
