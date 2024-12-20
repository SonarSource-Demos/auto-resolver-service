from handlers.files import map_issues_to_files, fix_file
from handlers.sonarqube import get_binding, get_issues
from handlers.integrations import get_integration, github as github_integration
from asyncio import gather

PR_BRANCH_NAME_TEMPLATE = 'sonar/autofix-pr-{pull_request}-{task_id}'


async def fix_pr_issues(server_url, task_id, project_key, pull_request, commit_hash, source_branch):
    valid, binding, integration, integration_url, branch = await validate_task(
        project_key=project_key,
        server_url=server_url,
        source_branch=source_branch,
        commit_hash=commit_hash
    )
    if not valid:
        return
    issues = await get_issues(server_url=server_url, project_key=project_key, pull_request_id=pull_request)
    pr_branch = await create_pr_branch(
        integration=integration,
        integration_url=integration_url,
        repository=binding['repository'],
        name=PR_BRANCH_NAME_TEMPLATE.format(pull_request=pull_request, task_id=task_id),
        branch=branch
    )

    fixes = [i for i in await gather(
        *[
            fix_file(
                server_url=server_url,
                integration=integration,
                integration_url=integration_url,
                pr_branch_name=pr_branch['name'],
                repository=binding['repository'],
                source_branch=source_branch,
                file_path=file_path,
                issues=issues
            ) for file_path, issues in map_issues_to_files(issues=issues).items()
        ]
    ) if i['fix_count'] > 0]
    if fixes:
        await create_or_update_pull_request(
            integration=integration,
            integration_url=integration_url,
            repository=binding['repository'],
            pr_branch_name=pr_branch['name'],
            target_branch_name=branch['name'],
            pull_request=pull_request,
            fixes=fixes
        )


async def create_or_update_pull_request(integration, integration_url, pull_request, repository, pr_branch_name,
                                        target_branch_name, fixes):
    fix_message = '\n'.join([f"Fixing {i['fix_count']} issues in {i['file_path']}" for i in fixes])
    if pr_branch_name != target_branch_name:
        await integration.create_pull_request(
            host=integration_url,
            repository=repository,
            source_branch=pr_branch_name,
            target_branch=target_branch_name,
            title=f"SonarQube Autofix PR for {pull_request}",
            body=fix_message,
        )
    else:
        pr = await github_integration.get_pull_request(repository=repository, pr_name=pull_request,
                                                       host=integration_url)
        await github_integration.update_pull_request(
            host=integration_url,
            repository=repository,
            pr_name=pull_request,
            body=pr['body'] + '\n' + fix_message
        )


async def create_pr_branch(integration, integration_url, repository, name, branch):
    if not branch['name'].startswith('sonar/autofix-pr-'):
        branch = await integration.create_branch(
            host=integration_url, repository=repository, branch_name=name, base_branch_name=branch['name']
        )
    return branch


async def validate_task(project_key, server_url, source_branch, commit_hash):
    valid = True
    binding = await get_binding(project_key=project_key, server_url=server_url)
    integration, integration_url = await get_integration(binding=binding)
    if not integration:
        valid = False
    branch = await github_integration.get_branch(
        host=integration_url,
        repository=binding['repository'],
        branch_name=source_branch
    )
    unused_var = ""
    if not branch or not await integration.validate_latest_commit(
            repository=binding['repository'], branch_name=source_branch,
            host=integration_url, branch=branch, commit_hash=commit_hash):
        valid = False
    return valid, binding, integration, integration_url, branch
