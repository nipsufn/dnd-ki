#!/usr/bin/env python3

import os
import sys

import argparse
import logging
import re
import requests

FEEDBACK = ""

def write(text):
    global FEEDBACK
    FEEDBACK += text + "\n"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", "-v", "--verbose", action="store_true",
                        help="debug mode")
    parser.add_argument("-i", "--ignore", nargs='+', type=str,
                        help="space separated list of files to be ignored",
                        default=list())
    args = parser.parse_args()

    logger = logging.getLogger('journal_tester')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    whitelist = [
        ".gitignore",
        "requirements.txt",
        ".travis.yml",
        "test.py",
        "tag.py"
        ]
    whitelist.extend(args.ignore)
    with open(".gitignore") as gitignore:
        whitelist.extend(gitignore.read().splitlines())
    logger.debug("main: Ignored files: %s", str(whitelist))
    files = [f for f in os.listdir() if os.path.isfile(f)]
    files = list(set(files) - set(whitelist))
    logger.debug("main: List of files: %s", str(files))

    tags = []
    refs = []

    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as file_stream:
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
                        write("Tag or reference malformed: " + match.group(0)
                              + "; line: " + str(line_no+1)
                              + "; position: " + str(match.start(0))
                              + "; file: " + file_path)
            if balance[0]%2 != 0:
                write("Unmatched \" in file: " + file_path)
            if balance[1] != balance[2]:
                write("Unmatched <> in file: " + file_path)
            if balance[3] != balance[4]:
                write("Unmatched () in file: " + file_path)
            if balance[5] != balance[6]:
                write("Unmatched [] in file: " + file_path)
            if merge_conflict:
                write("Merge conflict in file: " + file_path)

    for n, x in enumerate(tags):
        for o, y in enumerate(tags):
            if o > n and x[0] == y[0]:
                write("Duplicate tag found: " + y[0]
                      + "; first: line: " + str(x[1]+1)
                      + ", position: " + str(x[2])
                      + ", file: " + x[3]
                      + "; subsequent: line: " + str(y[1]+1)
                      + ", position: " + str(y[2])
                      + ", file: " + y[3])

    for ref in refs:
        for tag in tags:
            if ref[0] == tag[0]:
                ref[4] = True
        if not ref[4]:
            write("Reference malformed: " + ref[0]
                  + "; line: " + str(ref[1]+1)
                  + "; position: " + str(ref[2])
                  + "; file: " + ref[3])

    if 'CI' in os.environ:
        if FEEDBACK != "":
            requests.post('https://api.github.com/repos/'
                          + os.environ['TRAVIS_REPO_SLUG'] + '/commits/'
                          + os.environ['TRAVIS_COMMIT'] + '/comments',
                          json={"body": FEEDBACK},
                          auth=requests.auth.HTTPBasicAuth(
                              os.environ['github_user'],
                              os.environ['github_token']))
        else:
            requests.post('https://api.github.com/repos/'
                          + os.environ['TRAVIS_REPO_SLUG'] + '/commits/'
                          + os.environ['TRAVIS_COMMIT']+'/comments',
                          json={"body": "Test passed!"},
                          auth=requests.auth.HTTPBasicAuth(
                              os.environ['github_user'],
                              os.environ['github_token']))

    if FEEDBACK != "":
        print(FEEDBACK)
        sys.exit(1)
    else:
        print("Test passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
