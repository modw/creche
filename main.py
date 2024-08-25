import yaml
import importlib
from dataclasses import dataclass
from typing import Dict


@dataclass
class AppConfig:
    template: str
    style: str
    data: Dict[str, str]
    parameters: dict


def load_config() -> AppConfig:
    with open("./config/config.yaml", "r") as config_file:
        config_dict = yaml.safe_load(config_file)
    return AppConfig(**config_dict)


if __name__ == "__main__":
    config = load_config()

    # Import chosen template
    template = importlib.import_module(
        f"templates.{config.template}", package=__name__
    )

    # Use the imported template
    app = template.ChildcareCostEstimator(config)
    app.run()
