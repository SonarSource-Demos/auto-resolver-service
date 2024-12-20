from asyncio import gather
from collections import defaultdict
from handlers.sonarqube import get_codefix, get_codefix_availability

def map_issues_to_files(issues):
    files = defaultdict(list)
    for issue in issues:
        files[issue['component'].split(':')[-1]].append(issue)
    return files


async def fix_file(server_url, integration, integration_url, repository, source_branch, file_path, pr_branch_name,
                   issues):
    available_fixes, (sha, content) = await gather(
        get_issue_fixes(issues=issues, server_url=server_url),
        integration.get_content(
            host=integration_url,
            repository=repository,
            branch=source_branch,
            file_path=file_path
        )
    )
    fix_count = 0
    if available_fixes and content:
        fix_count, message, results = apply_fixes(content=content, fixes=available_fixes)
        await integration.update_file(host=integration_url, repository=repository, message=message,
                                             file_path=file_path, content=results, sha=sha, branch_name=pr_branch_name)
    return dict(file_path=file_path, fix_count=fix_count)

async def get_issue_fixes(server_url, issues):
    fixable_issues = [
        i for i in await gather(
            *[get_codefix_availability(server_url=server_url, issue_id=issue['key']) for issue in issues]
        ) if i
    ]
    fixes = await gather(*[get_codefix(server_url=server_url, issue_id=issue_id) for issue_id in fixable_issues])
    return fixes

def apply_fixes(content, fixes):
    changed_lines = set()
    content_map = {int(idx + 1): line for idx, line in enumerate(content.splitlines())}
    messages = list()
    fix_count = 0
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
        fix_count += 1
    return fix_count, '\n'.join(messages), '\n'.join([line for _, line in sorted(content_map.items())])
