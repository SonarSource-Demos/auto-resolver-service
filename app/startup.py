import os
from httpx import AsyncClient
from github import Auth
from github import Github

from parrot_api.core import get_settings, configure_default_log_attributes

app_settings = get_settings(env_folder=os.getenv('SETTINGS_FOLDER', '/apps/settings'))

configure_default_log_attributes(attributes=dict(
    service_name=app_settings['service_name'],
    environment=app_settings['environment']
))
current_directory = os.path.abspath(__file__).replace('startup.py', '')
github_client = Github(auth=Auth.Token(app_settings['github_token']))
sonarqube_client = AsyncClient(base_url=app_settings['sonarqube_url'], headers={
    "Authorization": "Bearer " + app_settings['sonarqube_token']
})