import uvicorn
import sys
from pathlib import Path

# Add project root to PYTHONPATH
project_root = str(Path(__file__).parent.absolute())
sys.path.append(project_root)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info"
    ) 