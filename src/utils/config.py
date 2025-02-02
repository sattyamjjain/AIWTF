import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration management"""

    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
