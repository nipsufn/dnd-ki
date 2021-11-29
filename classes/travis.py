# travis.py
"""Helper module for repo operations inside TravisCI environment
"""
import os
import requests
from classes.console import Console

class Travis:
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
                    Travis.git_dir)
        Console.run('git config --global user.name "' + user + '"',
                    Travis.git_dir)

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
        Console.run('git remote rm origin')
        Console.run('git remote add origin '
                    + 'https://${GH_USER}:${GH_TOKEN}@github.com/'
                    + repo_slug + '.git > /dev/null 2>&1')

    @staticmethod
    def git_clone(repo_slug):
        """git clone
        Args:
            repo_slug (str): "user/repo", defaults to the one used
                by Travis
        """
        if 'CI' not in os.environ:
            return
        Console.run('git clone '
                    + 'https://${GH_USER}:${GH_TOKEN}@github.com/'
                    + repo_slug + '.git > /dev/null 2>&1')

    @staticmethod
    def git_checkout(branch):
        """git checkout
        Args:
            branch (str): branch name
        Returns:
            bool: non-False if script is running on Travis CI
        """
        if 'CI' not in os.environ:
            return False
        if not repo_slug:
            repo_slug = os.environ['TRAVIS_REPO_SLUG']
        Console.run('cd ' + Travis.git_dir)
        Console.run('git fetch', Travis.git_dir)
        Console.run('git checkout ' + branch, Travis.git_dir)
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
        Console.run('git add ' + pathspec, Travis.git_dir)

        return Console.run('git rev-parse HEAD', Travis.git_dir)

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
                        Travis.git_dir)
        else:
            Console.run('git commit -am "' + message + '"', Travis.git_dir)

        return Console.run('git rev-parse HEAD', Travis.git_dir)

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
        Console.run('git push origin $(git rev-parse --abbrev-ref HEAD):'
                    + target_branch
                    + ' --quiet',
                    Travis.git_dir)
        return Console.run('git rev-parse HEAD', Travis.git_dir)

    @staticmethod
    def git_comment(message, commit=None, repo_slug=None):
        if 'CI' not in os.environ:
            return False
        if not commit:
            commit = os.environ['TRAVIS_COMMIT']
        if not repo_slug:
            repo_slug = os.environ['TRAVIS_REPO_SLUG']
        request = requests.post('https://api.github.com/repos/'
                                + repo_slug + '/commits/'
                                + commit.rstrip() + '/comments',
                                json={"body": message},
                                auth=requests.auth.HTTPBasicAuth(
                                    os.environ['GH_USER'],
                                    os.environ['GH_TOKEN']))
        return request.ok
