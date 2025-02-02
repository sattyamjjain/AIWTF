import logging.config
import yaml
from pathlib import Path

def setup_logging(
    default_path='config/logging.yaml',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration"""
    path = default_path
    if Path(path).exists():
        with open(path, 'rt') as f:
            try:
                config = yaml.safe_load(f.read())
                # Ensure logs directory exists
                Path("logs").mkdir(exist_ok=True)
                logging.config.dictConfig(config)
            except Exception as e:
                print(f"Error in Logging Configuration: {e}")
                logging.basicConfig(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        
    return logging.getLogger(__name__)
