"""
Configuration loader for the Loan Default Risk Pipeline
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any


class Config:
    """Configuration management class"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to config.yaml file
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        # Load environment variables
        env_path = Path(__file__).parent.parent / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # Load YAML configuration
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Substitute environment variables
        self._substitute_env_vars(self._config)
    
    def _substitute_env_vars(self, config: Any) -> None:
        """Recursively substitute environment variables in config"""
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    config[key] = os.getenv(env_var, value)
                elif isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
        elif isinstance(config, list):
            for item in config:
                self._substitute_env_vars(item)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation)
        
        Args:
            key: Configuration key (e.g., 'kafka.bootstrap_servers')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return self._config.copy()
    
    @property
    def kafka_config(self) -> Dict[str, Any]:
        """Get Kafka configuration"""
        return self.get('kafka', {})
    
    @property
    def spark_config(self) -> Dict[str, Any]:
        """Get Spark configuration"""
        return self.get('spark', {})
    
    @property
    def storage_config(self) -> Dict[str, Any]:
        """Get storage configuration"""
        return self.get('storage', {})
    
    @property
    def mlflow_config(self) -> Dict[str, Any]:
        """Get MLflow configuration"""
        return self.get('mlflow', {})
    
    @property
    def api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self.get('apis', {})


# Global config instance
config = Config()
