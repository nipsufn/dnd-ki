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
    def git_unbork_gha_root(repo_slug=None):
        """git remove and re-add origin
        Args:
            repo_slug (str, optional): "user/repo", defaults to the one used
                by GHA
        """
        if 'CI' not in os.environ:
            return
        if not repo_slug:
            repo_slug = os.environ['GITHUB_REPOSITORY']
        token = os.environ['GH_TOKEN']
        Console.run('git remote set-url origin https://'
                    + token + '@github.com/'
                    + repo_slug + '.git > /dev/null 2>&1')

    @staticmethod
    def git_clone(repo_slug):
        """git clone
        Args:
            repo_slug (str): "user/repo", defaults to the one used
                by GHA
        """
        if 'CI' not in os.environ:
            return
        token = os.environ['GH_TOKEN']
        Console.run('git clone '
                    + 'https://'
                    + token + '@github.com/'
                    + repo_slug + '.git > /dev/null 2>&1')

    @staticmethod
    def git_checkout(branch):
        """git checkout
        Args:
            branch (str): branch name
        Returns:
            bool: non-False if script is running on GHA CI
        """
        if 'CI' not in os.environ:
            return False
        Console.run('cd ' + GHA.git_dir)
        Console.run('git fetch', GHA.git_dir)
        Console.run('git checkout ' + branch, GHA.git_dir)
        return True

    @staticmethod
    def git_add(pathspec):
        """git add `pathspec` from current branch in git_dir to target_branch
        Args:
            pathspec (str): files to add, can be a fileglob
        Returns:
            str: commit hash or False
        """
        if 'CI' not in os.environ:
            return False
        Console.run('git add ' + pathspec, GHA.git_dir)

        return Console.run('git rev-parse HEAD', GHA.git_dir)

    @staticmethod
    def git_commit_all(message, sanitize=True):
        """git commit from current branch in git_dir to target_branch
        Args:
            message (str): branch name to push to
            sanitize (bool, optional): whether to bash-sanitize message,
                defaults to True
        Returns:
            str: commit hash or False
        """
        if 'CI' not in os.environ:
            return False
        if sanitize:
            Console.run('git commit -am "' + message.replace('"', '\\"') + '"',
                        GHA.git_dir)
        else:
            Console.run('git commit -am "' + message + '"', GHA.git_dir)

        return Console.run('git rev-parse HEAD', GHA.git_dir)

    @staticmethod
    def git_push(target_branch='master'):
        """force git push from current branch in git_dir to target_branch
        Args:
            target_branch (str): branch name to push to
        Returns:
            str: commit hash or False
        """
        if 'CI' not in os.environ:
            return False
        Console.run('pwd', GHA.git_dir)
        Console.run('env', GHA.git_dir)
        Console.run('cat .git/config', GHA.git_dir)
        Console.run('git push origin $(git rev-parse --abbrev-ref HEAD):'
                    + target_branch
                    + ' --quiet',
                    GHA.git_dir)
        return Console.run('git rev-parse HEAD', GHA.git_dir)

    @staticmethod
    def git_get_commit():
        """get latest git commit message from current branch/repo
        Returns:
            str: commit hash or False
        """
        if 'CI' not in os.environ:
            return False
        return Console.run('git log -1 --pretty=%B', GHA.git_dir)

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
                                auth=requests.auth.HTTPBasicAuth(
                                    os.environ['GH_USER'],
                                    os.environ['GH_TOKEN']))
        return request.ok
