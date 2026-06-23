"""Configuration management for lrc-tools."""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


@dataclass
class ProcessorConfig:
    max_phrase_duration: float = 2.5
    min_phrase_duration: float = 0.3
    max_words_per_phrase: int = 8
    split_on_commas: bool = True
    use_onset_detection: bool = False
    onset_blend_factor: float = 0.5


@dataclass
class VisualizerConfig:
    default_font: str = "block"
    refresh_rate: float = 0.05
    word_display_time: float = 0.3
    transition_style: str = "instant"
    colors_enabled: bool = True
    clear_screen: bool = True


@dataclass
class PullerConfig:
    search_threads: int = 5
    download_threads: int = 5
    request_delay: float = 0.05
    max_retries: int = 3
    retry_backoff: float = 0.5
    prefer_synced: bool = True
    preserve_structure: bool = True
    overwrite: bool = False


class Config:
    def __init__(self, config_file: Optional[Path] = None):
        self.processor = ProcessorConfig()
        self.visualizer = VisualizerConfig()
        self.puller = PullerConfig()
        if config_file and config_file.exists():
            self.load(config_file)

    def load(self, config_file: Path):
        if config_file.suffix in ['.yaml', '.yml']:
            if not _HAS_YAML:
                raise ImportError("PyYAML is required to load .yaml config files")
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
        elif config_file.suffix == '.json':
            with open(config_file, 'r') as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_file.suffix}")

        if 'processor' in data:
            for key, value in data['processor'].items():
                if hasattr(self.processor, key):
                    setattr(self.processor, key, value)
        if 'visualizer' in data:
            for key, value in data['visualizer'].items():
                if hasattr(self.visualizer, key):
                    setattr(self.visualizer, key, value)
        if 'puller' in data:
            for key, value in data['puller'].items():
                if hasattr(self.puller, key):
                    setattr(self.puller, key, value)

    def save(self, config_file: Path):
        data = {
            'processor': asdict(self.processor),
            'visualizer': asdict(self.visualizer),
            'puller': asdict(self.puller),
        }
        if config_file.suffix in ['.yaml', '.yml']:
            with open(config_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        elif config_file.suffix == '.json':
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {config_file.suffix}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'processor': asdict(self.processor),
            'visualizer': asdict(self.visualizer),
            'puller': asdict(self.puller),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        config = cls()
        if 'processor' in data:
            for key, value in data['processor'].items():
                if hasattr(config.processor, key):
                    setattr(config.processor, key, value)
        if 'visualizer' in data:
            for key, value in data['visualizer'].items():
                if hasattr(config.visualizer, key):
                    setattr(config.visualizer, key, value)
        if 'puller' in data:
            for key, value in data['puller'].items():
                if hasattr(config.puller, key):
                    setattr(config.puller, key, value)
        return config
