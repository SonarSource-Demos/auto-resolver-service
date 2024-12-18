from starlette.responses import JSONResponse
from starlette.background import BackgroundTask
from handlers.files import process_file_issues


async def process_webhook_request(body):
    from handlers.webhooks import process_webhook
    results = await process_webhook(**body)
    background_task = BackgroundTask(
        process_file_issues,
        project=results['projectKey'],
        source_branch=results['source_branch'],
        target_branch=results['target_branch'],
        file_mapping=results['file_mapping'],
    )
    for file, issues in results['file_mapping'].items():
        background_tasks.add_task(
            process_file_issues,
            project=results['projectKey'],
            source_branch=results['source_branch'],
            target_branch=results['target_branch'],
            file=file,
            issues=issues,
        )
    return JSONResponse(content=dict(isActive=True, response=results), background=background_task)
