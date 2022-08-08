# GHA.py
"""Helper module for repo operations inside GHA CI environment
"""
import os
import requests

def git_comment(message, commit=None, repo_slug=None) -> bool:
    """post a comment on a commit
    Optional args will be pulled from CI Environment variables if possible
    Args:
        message (str): message to post
        commit (str, optional): SHA checksum of commit
        repo_slug (str, optional): string of 'user/repo'
    Returns:
        bool: if HTTP request to post comment succeeded True
    """
    if 'CI' not in os.environ:
        return False
    if not commit:
        commit = os.environ['GITHUB_SHA']
    if not repo_slug:
        repo_slug = os.environ['GITHUB_REPOSITORY']
    request = requests.post('https://api.github.com/repos/'
                            + repo_slug + '/commits/'
                            + commit.rstrip() + '/comments',
                            json={"body": message},
                            headers={"authorization":"Bearer " + os.environ['GH_TOKEN']}
                            )
    return request.ok
