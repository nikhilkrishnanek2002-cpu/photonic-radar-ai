#!/bin/bash
# demo_runner.sh - Helper script to run the PHOENIX demo with various options
# Usage: ./demo_runner.sh [option]

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directory
PROJECT_DIR="/home/nikhil/PycharmProjects/photonic-radar-ai"
DEMO_FILE="$PROJECT_DIR/demo.py"

# Check if demo exists
if [ ! -f "$DEMO_FILE" ]; then
    echo -e "${RED}✗ demo.py not found at $DEMO_FILE${NC}"
    exit 1
fi

# Function to show menu
show_menu() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         PHOENIX Radar AI - Demo Runner Menu                ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
    
    echo "Select demo type:"
    echo -e "  ${GREEN}1${NC}) Quick demo (10 seconds)"
    echo -e "  ${GREEN}2${NC}) Standard demo (20 seconds, default)"
    echo -e "  ${GREEN}3${NC}) Extended demo (60 seconds)"
    echo -e "  ${GREEN}4${NC}) Long demo (5 minutes)"
    echo -e "  ${GREEN}5${NC}) Custom duration"
    echo -e "  ${GREEN}6${NC}) Debug mode (verbose output)"
    echo -e "  ${GREEN}7${NC}) Run + Save to file"
    echo -e "  ${GREEN}8${NC}) Show help"
    echo -e "  ${GREEN}q${NC}) Quit"
    echo ""
}

# Function to run demo
run_demo() {
    local duration=$1
    local verbose=$2
    
    echo -e "\n${GREEN}Starting PHOENIX Demo...${NC}"
    echo -e "Duration: ${YELLOW}${duration}s${NC}"
    
    cd "$PROJECT_DIR"
    
    if [ "$verbose" = "true" ]; then
        python3 "$DEMO_FILE" --duration "$duration" --verbose
    else
        python3 "$DEMO_FILE" --duration "$duration"
    fi
}

# Main loop
if [ $# -eq 0 ]; then
    # Interactive mode
    while true; do
        show_menu
        read -p "Enter choice: " choice
        
        case $choice in
            1)
                run_demo 10 false
                ;;
            2)
                run_demo 20 false
                ;;
            3)
                run_demo 60 false
                ;;
            4)
                run_demo 300 false
                ;;
            5)
                read -p "Enter duration in seconds: " duration
                run_demo "$duration" false
                ;;
            6)
                run_demo 20 true
                ;;
            7)
                read -p "Enter filename to save to: " filename
                if [ -z "$filename" ]; then
                    filename="demo_output_$(date +%Y%m%d_%H%M%S).txt"
                fi
                echo -e "\n${GREEN}Saving output to: $filename${NC}"
                cd "$PROJECT_DIR"
                python3 "$DEMO_FILE" --duration 60 > "$filename" 2>&1
                echo -e "${GREEN}✓ Saved to $(pwd)/$filename${NC}"
                echo -e "Size: $(wc -l < "$filename") lines"
                ;;
            8)
                echo -e "\n${BLUE}PHOENIX Radar AI - Demo Help${NC}\n"
                python3 "$DEMO_FILE" --help
                ;;
            q|Q)
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                ;;
        esac
        
        read -p "Press Enter to continue..."
    done
else
    # Command-line mode
    case $1 in
        quick)
            run_demo 10 false
            ;;
        standard)
            run_demo 20 false
            ;;
        extended)
            run_demo 60 false
            ;;
        long)
            run_demo 300 false
            ;;
        debug)
            run_demo 20 true
            ;;
        help|--help|-h)
            python3 "$DEMO_FILE" --help
            ;;
        *)
            echo "Usage: $0 [quick|standard|extended|long|debug|help]"
            echo ""
            echo "Examples:"
            echo "  $0 quick        # 10-second demo"
            echo "  $0 standard     # 20-second demo"
            echo "  $0 extended     # 60-second demo"
            echo "  $0 long         # 5-minute demo"
            echo "  $0 debug        # 20-second with debug output"
            echo "  $0 help         # Show help"
            echo ""
            echo "Or run without arguments for interactive menu:"
            echo "  $0"
            ;;
    esac
fi
