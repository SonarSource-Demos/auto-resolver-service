from parrot_api.core import log_event

from handlers.sonarqube import get_binding
from startup import github_client
from asyncio import gather
from handlers.sonarqube import get_codefix_availability, get_codefix


async def process_file_issues(project, task_id, pull_request, source_branch, file_mapping):
    binding = await get_binding(project_key=project)
    if not binding:
        return
    updates = {
        fixed_file: dict(
            message=message,
            content=content,
            sha=sha,
            issue_count=issue_count
        ) for issue_count, fixed_file, sha, message, content in await gather(
            *[
                fix_file(
                    repository=binding['repository'],
                    source_branch=source_branch,
                    file=file,
                    issues=issues
                ) for file, issues in file_mapping.items()
            ]
        ) if issue_count > 0
    }

    if updates:
        await create_pull_request(repository=binding['repository'], task_id=task_id, source_branch=source_branch,
                                  pull_request=pull_request, updates=updates)


async def fix_file(repository, source_branch, file, issues):
    sha, content = await get_file_content(repository=repository, source_branch=source_branch, file=file)
    updated = 0
    if not content:
        return updated, file, sha, None, None
    available_fixes = await get_issue_fixes(issues=issues)
    if available_fixes:
        updated = len(available_fixes)
    message, results = apply_fixes(file=file, content=content, fixes=available_fixes)
    return updated, file, sha, message, results


async def get_file_content(repository, source_branch, file):
    repo = github_client.get_repo(repository)
    content = repo.get_contents(path=file, ref=source_branch)
    return content.sha, content.decoded_content.decode()


async def get_issue_fixes(issues):
    fixable_issues = [
        i for i in await gather(*[get_codefix_availability(issue_id=issue['key']) for issue in issues]) if i
    ]
    fixes = await gather(*[get_codefix(issue_id=issue_id) for issue_id in fixable_issues])
    return fixes


def apply_fixes(file, content, fixes):
    changed_lines = set()
    content_map = {int(idx+1): line for idx, line in enumerate(content.splitlines())}
    messages = list()
    for fix in fixes:
        line_changes = set(
            [line for change in fix['changes'] for line in range(change['startLine'], change['endLine'] + 1)])
        if line_changes & changed_lines:
            continue
        else:
            for line in line_changes:
                del content_map[line]
        messages.append(fix['explanation'])
        for change in fix['changes']:
            content_map[change['startLine']] = change['newCode']
        changed_lines = changed_lines.union(line_changes)
    return '\n'.join(messages), '\n'.join([line for _, line in sorted(content_map.items())])


async def create_pull_request(repository, task_id, source_branch, pull_request, updates):
    repo = github_client.get_repo(repository)
    branch_name = f'sonarfix-pr-{pull_request}-{task_id}'
    sha = repo.get_branch(branch=source_branch).commit.sha
    ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sha)

    pr_messages = [

    ]
    unused_var = 'thing'
    for file, update in updates.items():
        log_event(level='WARNING', status='failure', process_type='update_file',
                  payload=dict(file=file, keys=file))
        file = repo.update_file(
            path=file,
            message=update['message'],
            content=update['content'],
            sha=update['sha'],
            branch=branch_name
        )
        sha = file['commit'].sha
        pr_messages.append(
            f"Fixed {update['issue_count']} {'issue' if update['issue_count'] == 1 else 'issues'} in {file}")
    pr = repo.create_pull(
        base=source_branch, head=ref.ref, title=f"SonarQube Auto PR Fixes for PR {pull_request}",
        body='\n'.join(pr_messages)
    )
    return pr
