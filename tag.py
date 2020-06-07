#!/usr/bin/env python3
"""
This script creates cross-referencing tags in md files
"""
import os
import sys
import subprocess
import argparse
import logging
import re
from html.parser import HTMLParser
import time
import requests

class TickTock:
    __ticktock = float()
    @staticmethod
    def tick():
        TickTock.__ticktock = time.time()
    @staticmethod
    def tock():
        return time.time() - TickTock.__ticktock

class TagParser(HTMLParser):
    def __init__(self):
        self.tags = []
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attr_dict = dict(attrs)
        if 'href' in attr_dict.keys():
            return
        if 'id' not in attr_dict.keys():
            return
        if 'pattern' in attr_dict.keys():
            pattern_list = sorted(attr_dict['pattern'].split(','), key=len,
                                  reverse=True)
            regex = '|'.join(pattern_list) if pattern_list \
                else attr_dict['pattern']
            regex = regex.replace(r"*", r"\w{0,7}")

            self.tags.append([attr_dict['id'], regex])
        elif 'regex' in attr_dict.keys():
            self.tags.append([attr_dict['id'], attr_dict['regex']])
        else:
            return
    def error(self, message):
        return

class TagCreator(HTMLParser):
    def __init__(self, tags):
        self.current_html_tag = []
        self.tags = tags
        self.text = ""
        super().__init__()

    def handle_starttag(self, tag, attrs):
        self.current_html_tag.append(tag)
        self.text += self.get_starttag_text()

    def handle_endtag(self, tag):
        if len(self.current_html_tag) == 0 or self.current_html_tag[0] == tag:
            self.current_html_tag.pop()
        if tag == "br":
            return
        self.text += "</" + tag + ">"

    def handle_data(self, data):
        if len(self.current_html_tag) == 0:
            for pair in self.tags:
                #all user-tags `{whatever}Actual Name` or `[whatever](Actual Name)`
                regex = r"[\{\[]([ \"\w]+?)[\}\]]\(?(" + pair[1] + r")\)?"
                substitute = r"[\1](#" + pair[0] + r")"
                data = re.sub(regex, substitute, data)

                #all standard tags unless it is already tagged [] or in between ><
                regex = r"([ (])(" + pair[1] +r")([ ,.)?!:;\"\n])"
                substitute = r"\1[\2](#" + pair[0] + r")\3"
                data = re.sub(regex, substitute, data)
        self.text += data

    def clean(self):
        self.text = ""

    def error(self, message):
        return

class Console:
    __logger = None
    @staticmethod
    def __init__(loglevel=logging.WARN):
        logging.TRACE = 5
        logging.addLevelName(5, "TRACE")
        Console.__logger = logging.getLogger('console')
        setattr(Console.__logger, 'trace',
                lambda *args: Console.__logger.log(5, *args))

        log_handler = logging.StreamHandler()
        log_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        Console.__logger.addHandler(log_handler)
        Console.__logger.setLevel(loglevel)

    @staticmethod
    def run(command, pwd=None, return_stderr=False):
        if not Console.__logger:
            Console.__init__()
        if pwd:
            command = 'cd ' + pwd + ' && ' + command
        Console.__logger.debug("Running command %s", command)
        result = subprocess.run(command, capture_output=True, shell=True,
                                check=False)
        for line in result.stdout.decode('utf-8').splitlines():
            Console.__logger.debug(line)
        for line in result.stderr.decode('utf-8').splitlines():
            Console.__logger.warning(line)
        if return_stderr:
            return (result.stdout.decode('utf-8'),
                    result.stderr.decode('utf-8'))
        return result.stdout.decode('utf-8')

    @staticmethod
    def set_log_level(loglevel):
        if not Console.__logger:
            Console.__init__()
        Console.__logger.setLevel(loglevel)

def prepare_logger(args):
    logging.TRACE = 5
    logging.addLevelName(5, "TRACE")
    logger = logging.getLogger('journal_tagger')
    setattr(logger, 'trace', lambda *args: logger.log(5, *args))

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)
    if args.trace:
        logger.setLevel(logging.TRACE)
        Console.set_log_level(logging.TRACE)
    elif args.debug:
        logger.setLevel(logging.DEBUG)
        Console.set_log_level(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        Console.set_log_level(logging.INFO)
    return logger

def prepare_files(args, whitelist, logger):
    whitelist.extend(args.ignore)
    with open(".gitignore") as gitignore:
        whitelist.extend(gitignore.read().splitlines())
    logger.debug("Ignored files: %s", str(whitelist))
    files = [f for f in os.listdir() if os.path.isfile(f)]
    files = list(set(files) - set(whitelist))
    logger.trace("List of files: %s", str(files))
    return files

class Travis:
    git_dir = ''
    @staticmethod
    def git_setup(user="Travis CI", email="travis@travis-ci.org"):
        """git config --global user.email, user.name
        Args:
            user (str, optional): username, defaults to "Travis CI"
            email (str, optional): e-mail, defaults to "travis@travis-ci.org"
        """
        if 'CI' not in os.environ:
            return
        Console.run('git config --global user.email "' + email + '"',
                    Travis.git_dir)
        Console.run('git config --global user.name "' + user + '"',
                    Travis.git_dir)

    @staticmethod
    def git_unbork_travis_root(repo_slug=None):
        """git remove and re-add origin
        Args:
            repo_slug (str, optional): "user/repo", defaults to the one used
                by Travis
        """
        if 'CI' not in os.environ:
            return
        if not repo_slug:
            repo_slug = os.environ['TRAVIS_REPO_SLUG']
        Console.run('git remote rm origin')
        Console.run('git remote add origin '
                    + 'https://${github_user}:${github_token}@github.com/'
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
                    + 'https://${github_user}:${github_token}@github.com/'
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
                                    os.environ['github_user'],
                                    os.environ['github_token']))
        return request.ok

def process_tags(files, logger, prefix=""):
    TickTock.tick()
    tag_retriever = TagParser()
    # pass 1 - generate tags
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as file_stream:
            tag_retriever.feed(file_stream.read())

    logger.debug("Tag count: %s", str(len(tag_retriever.tags)))
    # pass 2 - use tags to create links
    write_time = 0.0
    logger.info("Tag lookup time: {:.5f}sec".format(TickTock.tock()))

    for file_path in files:
        text = None
        logger.trace(file_path)
        with open(file_path, 'r', encoding='utf-8') as file_stream:
            TickTock.tick()
            text = file_stream.read()
            tagger = TagCreator(tag_retriever.tags)
            tagger.feed(text)
            logger.trace("processing time: {:.5f}sec".format(TickTock.tock()))
            write_time += TickTock.tock()
            tagger.close()
            text = tagger.text

        file_path = prefix + file_path
        with open(file_path, 'w', encoding='utf-8') as file_stream:
            file_stream.write(text)
    logger.info("tag writing time: {:.5f}sec".format(write_time))

def test_files(files, prefix=""):
    tags = []
    refs = []
    feedback = ""

    for file_path in files:
        with open(prefix + file_path, 'r', encoding='utf-8') as file_stream:
            balance = [0 for x in range(7)]
            merge_conflict = False
            for line_no, line_text in enumerate(file_stream):
                balance[0] += line_text.count('"')
                balance[1] += line_text.count('<')
                balance[2] += line_text.count('>')
                balance[3] += line_text.count('(')
                balance[4] += line_text.count(')')
                balance[5] += line_text.count('[')
                balance[6] += line_text.count(']')
                if re.search(r"\(\?<!", line_text):
                    balance[1] -= 1
                if re.match(r"[<>=]{7}", line_text):
                    merge_conflict = True
                if re.match(r"^(\t| )*>", line_text):
                    balance[2] -= 1
                for match in re.finditer(r"[a-zA-Z0-9](_[a-zA-Z0-9]+)+",
                                         line_text):
                    if re.search(r"<a id='[a-zA-Z0-9](_[a-zA-Z0-9]+?)+?'",
                                 line_text[match.start(0)-7:match.end(0)+6]):
                        tags.append([match.group(0), line_no, match.start(0),
                                     file_path])
                    elif re.search(r"<a id=\"[a-zA-Z0-9](_[a-zA-Z0-9]+?)+?\"",
                                   line_text[match.start(0)-7:match.end(0)+6]):
                        tags.append([match.group(0), line_no, match.start(0),
                                     file_path])
                    elif re.search(
                            r"\[[^\[^\]]+?\]\(#[a-zA-Z0-9](_[a-zA-Z0-9]+)+\)",
                            line_text[0:match.end(0)+1]):
                        refs.append([match.group(0), line_no, match.start(0),
                                     file_path, False])
                    elif re.search(r'<a href="[^"]+?(_[a-zA-Z0-9]+)+">.+?</a>',
                                   line_text):
                        continue
                    elif re.search(r"\[[^\[^\]]+?\]\(http.+?\)",
                                   line_text[0:match.end(0)+1]):
                        continue
                    else:
                        feedback += ("Tag or reference malformed: "
                                     + match.group(0)
                                     + "; line: " + str(line_no+1)
                                     + "; position: " + str(match.start(0))
                                     + "; file: " + file_path + "\n")

            if balance[0]%2 != 0:
                feedback += "Unmatched \" in file: " + file_path + "\n"
            if balance[1] != balance[2]:
                feedback += "Unmatched <> in file: " + file_path + "\n"
            if balance[3] != balance[4]:
                feedback += "Unmatched () in file: " + file_path + "\n"
            if balance[5] != balance[6]:
                feedback += "Unmatched [] in file: " + file_path + "\n"
            if merge_conflict:
                feedback += "Merge conflict in file: " + file_path + "\n"

    for n, x in enumerate(tags):
        for o, y in enumerate(tags):
            if o > n and x[0] == y[0]:
                feedback += ("Duplicate tag found: " + y[0]
                             + "; first: line: " + str(x[1]+1)
                             + ", position: " + str(x[2])
                             + ", file: " + x[3]
                             + "; subsequent: line: " + str(y[1]+1)
                             + ", position: " + str(y[2])
                             + ", file: " + y[3]
                             + "\n")

    for ref in refs:
        for tag in tags:
            if ref[0] == tag[0]:
                ref[4] = True
        if not ref[4]:
            feedback += ("Reference malformed: " + ref[0]
                         + "; line: " + str(ref[1]+1)
                         + "; position: " + str(ref[2])
                         + "; file: " + ref[3]
                         + "\n")

    if not feedback:
        return "Test passed!"
    return feedback

def main():
    TickTock.tick()
    # argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-dd", "--trace", "-vv",
                        action="store_true", help="debug mode")
    parser.add_argument("-d", "--debug", "-v", "--verbose",
                        action="store_true", help="debug mode")
    parser.add_argument("-i", "--ignore", nargs='+', type=str,
                        help="space separated list of files to be ignored",
                        default=list())
    args = parser.parse_args()

    # variables
    whitelist = [
        ".gitignore",
        "local",
        "requirements.txt",
        ".travis.yml",
        "test.py",
        "tag.py"
        ]

    # code
    logger = prepare_logger(args)
    files = prepare_files(args, whitelist, logger)
    logger.info("Initialization time: {:.5f}sec".format(TickTock.tock()))
    feedback = test_files(files)
    # comment test result on source repo and bail if needed
    Travis.git_comment(feedback)
    if feedback != "Test passed!":
        for line in feedback.splitlines():
            logger.error(line)
        sys.exit(1)
    prefix = "local/"
    commit_message = ""
    if 'CI' in os.environ:
        prefix = "dnd-ki/"
        commit_message = os.environ['TRAVIS_COMMIT_MESSAGE']
        Travis.git_clone('nipsufn/dnd-ki')
    process_tags(files, logger, prefix)
    feedback = test_files(files, prefix)
    if feedback != "Test passed!":
        if 'CI' in os.environ:
            Travis.git_comment('Parsing failed: ' + feedback)
        for line in feedback.splitlines():
            logger.error(line)
        sys.exit(1)
    else:
        if 'CI' in os.environ:
            Travis.git_dir = os.environ['PWD'] + '/' + prefix
            # Travis.git_setup()
            Travis.git_add('*.md')
            Travis.git_commit_all('Parsed: ' + commit_message)
            commit = Travis.git_push()
            Travis.git_comment(feedback, commit, 'nipsufn/dnd-ki')
        sys.exit(0)

if __name__ == "__main__":
    main()
