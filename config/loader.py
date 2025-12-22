from __future__ import annotations
import os, re, yaml
from pathlib import Path
from .schema import AppConfig

_ENV = re.compile(r"\$\{([^}]+)\}")

def _expand(v):
    if isinstance(v, str):
        m = _ENV.search(v)
        return os.getenv(m.group(1), v) if m else v
    return v

def _walk(x):
    if isinstance(x, dict):  return {k: _walk(v) for k, v in x.items()}
    if isinstance(x, list):  return [_walk(i) for i in x]
    return _expand(x)

def load_config(path: str | Path = "config/config.yaml") -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig(**_walk(data))
