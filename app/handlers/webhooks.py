from handlers.sonarqube import get_pull_request


def validate_webhook(status, quality_gate, branch):
    valid = True
    if status != 'SUCCESS':
        valid = False
    if quality_gate.get('status') == "OK":
        valid = False
    if branch.get('type') != "PULL_REQUEST":
        valid = False
    return valid


async def process_webhook(server_url: str, task_id: str, project: dict, branch: dict, commit_hash: str):
    results = dict(
        project_key=project,
        task_id=task_id,
        commit_hash=commit_hash,
        pull_request=None,
        source_branch=None,
        target_branch=None,
    )
    pull_request = await get_pull_request(
        server_url=server_url,
        project_key=project['key'],
        pull_request_id=branch['name']
    )
    results['source_branch'] = pull_request.get('branch')
    results['target_branch'] = pull_request.get('base')
    results['pull_request'] = pull_request.get('key')
    return results
