from base64 import b64encode, b64decode

from common import safe_json_request
from startup import GITHUB_TOKEN
from urllib.parse import quote

DEFAULT_HOST = 'https://api.github.com'


def generate_headers():
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer " + GITHUB_TOKEN,
        "X-GitHub-Api-Version": "2022-11-28"
    }


async def get_content(repository, file_path, branch, host):
    url = f'{host}/repos/{repository}/contents/{quote(file_path)}'
    _, js = await safe_json_request(url=url, headers=generate_headers(), method='GET', params={'ref': branch})
    content = None
    sha = js.get('sha')
    if js.get('content') is not None:
        content = b64decode(js['content']).decode('utf-8')
    elif js.get('download_url') is not None:
        _, sub_js = await safe_json_request(url=js['download_url'], headers=generate_headers(), method='GET')
        content = sub_js['content']
    return sha, content


async def get_branch(repository, branch_name, host):
    url = f'{host}/repos/{repository}/branches/{branch_name}'
    _, js = await safe_json_request(url=url, headers=generate_headers(), method='GET')
    return js


async def get_commit(repository, commit_sha, host):
    url = f'{host}/repos/{repository}/git/commits/{commit_sha}'
    _, js = await safe_json_request(url=url, headers=generate_headers(), method='GET')
    return js


async def validate_latest_commit(repository, branch_name, host, branch, commit_hash):
    valid = branch['commit']['sha'] == commit_hash
    if not valid:
        commit = await get_commit(repository=repository, commit_sha=commit_hash, host=host)
        valid = any([i['sha'] == branch['commit']['sha'] for i in commit['parents']])
    return valid


async def create_branch(repository, branch_name, base_branch_name, host):
    url = f'{host}/repos/{repository}/git/refs'
    base_branch = await get_branch(host=host, repository=repository, branch_name=base_branch_name)
    payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": base_branch['commit']['sha']
    }
    _, js = await safe_json_request(url=url, headers=generate_headers(), method='POST', json=payload)
    js['name'] = branch_name
    return js


async def update_file(repository, message, branch_name, file_path, content: str, sha, host):
    url = f'{host}/repos/{repository}/contents/{quote(file_path)}'
    payload = {
        "message": message,
        "content": b64encode(content.encode('utf-8')).decode('utf-8'),
        "sha": sha,
        "branch": branch_name
    }
    _, js = await safe_json_request(url=url, headers=generate_headers(), method='PUT', json=payload,
                                    log_attributes=dict(file_path=file_path))
    return js


async def create_pull_request(repository, source_branch, target_branch, title, body, host):
    url = f'{host}/repos/{repository}/pulls'
    payload = {
        "title": title,
        "body": body,
        "head": source_branch,
        "base": target_branch
    }
    _, js = await safe_json_request(url=url, headers=generate_headers(), method='POST', json=payload)
    return js


async def get_pull_request(repository, pr_name, host):
    url = f'{host}/repos/{repository}/pulls/{pr_name}'
    _, js = await safe_json_request(url=url, headers=generate_headers(), method='GET')
    return js


async def update_pull_request(repository, pr_name, body, host):
    url = f'{host}/repos/{repository}/pulls/{pr_name}'
    _, js = await safe_json_request(url=url, headers=generate_headers(), method='PATCH', json=dict(body=body))
    return js
