# GHA.py
"""Helper module for repo operations inside GHA CI environment
"""
import os
import requests
from classes.console import Console

class GHA:
    """shell / api wrapper for operations on git(hub)"""
    git_dir = ''
    @staticmethod
    def git_setup(user="GitHub Actions", email="noreply@github.com"):
        """git config --global user.email, user.name
        Args:
            user (str, optional): username, defaults to "GitHub Actions"
            email (str, optional): e-mail, defaults to "noreply@github.com"
        """
        if 'CI' not in os.environ:
            return
        Console.run('git config --global user.email "' + email + '"',
                    GHA.git_dir)
        Console.run('git config --global user.name "' + user + '"',
                    GHA.git_dir)

    @staticmethod
    def git_comment(message, commit=None, repo_slug=None):
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
