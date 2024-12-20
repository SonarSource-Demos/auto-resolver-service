from handlers.integrations import github as github_integration

MAPPING = {
    'github': github_integration,
}

async def get_integration(binding):
    return MAPPING.get(binding.get('alm'), github_integration), 'https://api.github.com'

