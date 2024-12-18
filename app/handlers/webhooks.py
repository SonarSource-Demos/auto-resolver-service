from asyncio import gather
from handlers.sonarqube import get_pull_requests, get_task, get_issues


async def process_webhook(taskId, status, project, qualityGate=None, **kwargs):
    results = dict(
        project_key=project,
        task_id=taskId,
        file_mappings=dict(),
        source_branch=None,
        target_branch=None,
        pull_request=None
    )
    if status != 'SUCCESS' or qualityGate['status'] == "OK" or kwargs.get('branch', dict()).get('type') != "PULL_REQUEST":
        return project, dict()
    pull_request, issues = await gather(*[
        get_pull_requests(pull_request_id=kwargs['branch']['name'], project_key=project['key']),
        get_issues(pull_request_id=kwargs['branch']['name'], project_key=project['key']),
    ])
    results['source_branch'] = pull_request[0]['branch']
    results['target_branch'] = pull_request[0]['base']
    results['pull_request'] = pull_request[0]['key']
    results['file_mapping'] = generate_file_issue_mapping(project_key=project, issues=issues)
    return results


from collections import defaultdict


def generate_file_issue_mapping(project_key, issues):
    files = defaultdict(list)
    for issue in issues:
        files[issue['component'].split(':')[-1]].append(issue)
    return files
