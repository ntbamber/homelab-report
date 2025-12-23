import os
import re
import yaml
from pathlib import Path
from dotenv import load_dotenv
from .schema import AppConfig

def load_config(config_path: str = "config/config.yaml") -> AppConfig:
    load_dotenv()

    # 2. Resolve the path
    # If path is absolute, use it. If relative, anchor it to the project root.
    path = Path(config_path)
    if not path.is_absolute():
        root_dir = Path(__file__).parent.parent.parent
        path = root_dir / config_path

    if not path.exists():
        raise FileNotFoundError(f"Config file not found at: {path}")

    # 3. Read the file as plain text
    with open(path, "r") as f:
        content = f.read()

    # 4. MAGIC: Regex to find ${VAR_NAME} and replace with os.getenv('VAR_NAME')
    # Pattern looks for ${WORD}
    pattern = re.compile(r'\$\{([^}^:]+)\}')

    def replace_env(match):
        env_var = match.group(1)
        # Get the value from environment, or keep the original string if not found
        return os.getenv(env_var, match.group(0))

    expanded_content = pattern.sub(replace_env, content)

    # 5. Parse the modified YAML
    config_data = yaml.safe_load(expanded_content)

    # 6. Validate with Pydantic
    return AppConfig(**config_data)