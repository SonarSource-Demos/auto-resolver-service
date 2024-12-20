from startup import SONARQUBE_TOKEN
from common import safe_json_request

def generate_headers():
    return {"Authorization": "Bearer " + SONARQUBE_TOKEN}


async def get_binding(server_url, project_key):
    status, js = await safe_json_request(
        method='get',
        url=server_url + '/api/alm_settings/get_binding',
        params={'project': project_key},
        headers=generate_headers()
    )
    if status == 404:
        js = dict(repository='SonarSource-Demos/auto-resolver-service')
    return js


async def get_pull_request(server_url, project_key, pull_request_id):
    pull_request = dict()
    status, js = await safe_json_request(
        method='get',
        url=server_url + '/api/project_pull_requests/list',
        params={'project': project_key},
        headers=generate_headers()
    )
    pull_requests = [i for i in filter(lambda pr: pr['key'] == pull_request_id, js['pullRequests'])]
    if pull_requests:
        pull_request = pull_requests[0]
    return pull_request


async def get_issues(server_url, project_key, pull_request_id):
    status, js = await safe_json_request(
        method='get',
        url=server_url + '/api/issues/search',
        params={
            'components': project_key,
            'pullRequest': pull_request_id,
            "ps": 500,
            "issueStatuses": "OPEN",
            "s": "SEVERITY", "asc": "false"
        },
        headers=generate_headers()
    )
    return js['issues']


async def get_codefix_availability(server_url, issue_id):
    server_url = server_url if 'sonarcloud.io' not in server_url else 'https://api.sonarcloud.io'
    status, js = await safe_json_request(
        method='get',
        url=server_url + f'/api/v2/fix-suggestions/issues/{issue_id}',
        headers=generate_headers()
    )
    return issue_id if js['aiSuggestion'] == 'AVAILABLE' else None


async def get_codefix(server_url, issue_id):
    server_url = server_url if 'sonarcloud.io' not in server_url else 'https://api.sonarcloud.io'
    status, js = await safe_json_request(
        method='POST',
        url=server_url + '/api/v2/fix-suggestions/ai-suggestions',
        json=dict(issueId=issue_id),
        headers=generate_headers()
    )
    return js