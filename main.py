import yaml
import importlib

# Load configuration
with open('./config/config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Import chosen template
template_name = config['template']

template = importlib.import_module(
    f'templates.{template_name}', package=__name__)

# # Use the imported template
template.run(config=config)
