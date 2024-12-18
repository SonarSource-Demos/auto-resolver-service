from startup import app_settings
from parrot_api.core import safe_json_request


async def get_binding(project_key):
    status, js = await safe_json_request(
        method='get',
        url=app_settings['sonarqube_url'] + '/api/alm_settings/get_binding',
        params={'project': project_key},
        headers={"Authorization": "Bearer " + app_settings['sonarqube_token']})
    if status == 404:
        js = dict(repository='SonarSource-Demos/auto-resolver-service')
    return js


async def get_task(task_id):
    _, js = await safe_json_request(
        method='get',
        url=app_settings['sonarqube_url'] + '/api/ce/task',
        params={'id': task_id},
        headers={"Authorization": "Bearer " + app_settings['sonarqube_token']})
    return js


async def get_pull_requests(project_key, pull_request_id):
    _, js = await safe_json_request(
        method='get',
        url=app_settings['sonarqube_url'] + '/api/project_pull_requests/list',
        params={'project': project_key},
        headers={"Authorization": "Bearer " + app_settings['sonarqube_token']})
    return [i for i in filter(lambda pr: pr['key'] == pull_request_id, js['pullRequests'])]


async def get_issues(project_key, pull_request_id):
    _, js = await safe_json_request(
        method='get',
        url=app_settings['sonarqube_url'] + '/api/issues/search',
        params={
            'components': project_key,
            'pullRequest': pull_request_id,
            "ps": 500,
            "issueStatuses": "OPEN",
            "s": "SEVERITY", "asc": "false"
        },
        headers={"Authorization": "Bearer " + app_settings['sonarqube_token']})
    return js['issues']


async def get_codefix_availability(issue_id):
    _, js = await safe_json_request(
        method='get',
        url=app_settings['sonarqube_url'] + f'/api/v2/fix-suggestions/issues/{issue_id}',
        headers={"Authorization": "Bearer " + app_settings['sonarqube_token']})
    return issue_id if js['aiSuggestion'] == 'AVAILABLE' else None

async def get_codefix(issue_id):
    _, js = await safe_json_request(
        method='POST',
        url=app_settings['sonarqube_url'] + '/api/v2/fix-suggestions/ai-suggestions',
        json=dict(issueId=issue_id),
        headers={"Authorization": "Bearer " + app_settings['sonarqube_token']})
    return js