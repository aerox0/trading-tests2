"""Configuration management system"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for strategies and backtests"""

    def __init__(
        self, config_path: Optional[str] = None, config_dict: Optional[Dict] = None
    ):
        """Initialize configuration

        Args:
            config_path: Path to YAML config file
            config_dict: Dictionary with configuration (overrides file)
        """
        self.config = {}

        if config_path:
            self.load_from_file(config_path)

        if config_dict:
            self.update(config_dict)

    def load_from_file(self, config_path: str):
        """Load configuration from YAML file

        Args:
            config_path: Path to YAML file
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r") as f:
            self.config = yaml.safe_load(f) or {}

    def update(self, config_dict: Dict[str, Any]):
        """Update configuration with dictionary

        Args:
            config_dict: Dictionary of configuration values
        """
        self._deep_update(self.config, config_dict)

    def _deep_update(self, base: Dict, update: Dict):
        """Deep merge two dictionaries

        Args:
            base: Base dictionary to update
            update: Dictionary with updates
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support

        Args:
            key: Configuration key (supports 'nested.key' notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value with dot notation support

        Args:
            key: Configuration key (supports 'nested.key' notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, output_path: str):
        """Save configuration to YAML file

        Args:
            output_path: Path to save configuration
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary

        Returns:
            Configuration dictionary
        """
        return self.config.copy()

    def get_strategy_params(self) -> Dict[str, Any]:
        """Get strategy parameters

        Returns:
            Strategy parameters dictionary
        """
        return self.get("parameters", {})

    def get_asset_config(self) -> Dict[str, Any]:
        """Get asset configuration

        Returns:
            Asset configuration dictionary
        """
        return self.get("asset", {})

    def get_backtest_config(self) -> Dict[str, Any]:
        """Get backtest configuration

        Returns:
            Backtest configuration dictionary
        """
        return self.get("backtest", {})

    def __repr__(self) -> str:
        return f"Config(keys={list(self.config.keys())})"
