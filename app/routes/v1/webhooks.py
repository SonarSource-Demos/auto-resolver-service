from starlette.responses import JSONResponse
from starlette.background import BackgroundTask
from handlers.files import process_file_issues


async def process_webhook_request(body):
    from handlers.webhooks import process_webhook
    if body.get('status') != 'SUCCESS':
        return 204, None
    results = await process_webhook(**body)
    if not results['file_mapping']:
        return JSONResponse(
            content=dict(isActive=True, response=dict(task_id=body['taskId'], project=results['project_key'])))
    background_task = BackgroundTask(
        process_file_issues,
        task_id=body['taskId'],
        project=results['project_key'],
        pull_request=results['pull_request'],
        source_branch=results['source_branch'],
        file_mapping=results['file_mapping'],
    )
    return JSONResponse(content=dict(isActive=True, response=results), background=background_task)
