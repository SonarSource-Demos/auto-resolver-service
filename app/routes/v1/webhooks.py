from starlette.responses import JSONResponse
from starlette.background import BackgroundTask
from handlers.pull_requests import fix_pr_issues
from handlers.sonarqube import get_pull_request


async def process_webhook_request(body):
    from handlers.webhooks import validate_webhook
    server_url, task_id, status, quality_gate, branch, project, commit_hash = parse_webhook_body(body=body)
    background_task = None
    if validate_webhook(status=status, quality_gate=quality_gate, branch=branch):
        pull_request = await get_pull_request(
            server_url=server_url,
            project_key=project['key'],
            pull_request_id=branch['name']
        )
        background_task = BackgroundTask(
            fix_pr_issues,
            server_url=server_url,
            task_id=task_id,
            commit_hash=commit_hash,
            project_key=project['key'],
            pull_request=pull_request.get('key'),
            source_branch=pull_request.get('branch'),
        )
    return JSONResponse(content=dict(isActive=True, response=dict(
        taskId=task_id,
        processingFixes=True if background_task else False
    )), background=background_task)


def parse_webhook_body(body):
    server_url = body['serverUrl']
    task_id = body['taskId']
    status = body['status']
    quality_gate = body.get('qualityGate', dict())
    branch = body.get('branch', dict())
    project = body.get('project', dict())
    commit_hash = body.get('revision', None)
    return server_url, task_id, status, quality_gate, branch, project, commit_hash
