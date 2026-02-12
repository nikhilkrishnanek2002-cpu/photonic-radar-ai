from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parent
shared_state_path = project_root / "runtime" / "shared_state.json"

print(f"Reading from: {shared_state_path}")
if shared_state_path.exists():
    try:
        with open(shared_state_path, 'r') as f:
            data = json.load(f)
            print("Read successful!")
            print(f"Keys: {list(data.keys())}")
            print(f"Uptime: {data.get('uptime')}")
    except Exception as e:
        print(f"Read failed: {e}")
else:
    print("File does not exist")
