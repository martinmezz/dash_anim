import os
import json


# Load config.json
with open('config.json', 'r') as cfg:
    CONFIG = json.load(cfg)

# Set environment
if ('ENV' in os.environ) and (os.environ['ENV'] == 'DEVELOPMENT'):
    ENV = 'DEVELOPMENT'
else:
    ENV = 'PRODUCTION'