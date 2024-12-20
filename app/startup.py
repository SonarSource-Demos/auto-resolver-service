import os

from common import configure_default_log_attributes


configure_default_log_attributes(attributes=dict(
    service_name=os.getenv('SERVICE_NAME', 'auto-resolver-service'),
    environment=os.getenv('ENVIRONMENT', 'prod')
))

current_directory = os.path.curdir

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
SONARQUBE_TOKEN = os.environ['SONARQUBE_TOKEN']
SONARQUBE_URL = os.environ['SONARQUBE_URL']
