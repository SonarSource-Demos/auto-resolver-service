from asyncio import gather
from handlers.sonarqube import get_pull_requests, get_task, get_issues


async def process_webhook(task_id, status, project, quality_gate, **_):
    results = dict(
        project=project,
        task_id=task_id,
        file_mappings=dict(),
        source_branch=None,
        target_branch=None,
    )
    if status != 'SUCCESS' or quality_gate['status'] == "OK":
        return project, dict()
    task = await get_task(task_id=task_id)
    if not task.get('pullRequest'):
        return dict()
    pull_request, issues = await gather(*[
        get_pull_requests(pull_request_id=task['pullRequest'], project_key=project),
        get_issues(pull_request_id=task['pullRequest'], project_key=project),
    ])
    results['source_branch'] = pull_request[0]['branch']
    results['target_branch'] = pull_request[0]['base']
    results['file_mappings'] = generate_file_issue_mapping(project_key=project, issues=issues)
    return results


from collections import defaultdict


def generate_file_issue_mapping(project_key, issues):
    files = defaultdict(list)
    for issue in issues:
        files[issue['component'][len(project_key):]].append(issue)
    return files
