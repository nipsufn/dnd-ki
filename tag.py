#!/usr/bin/env python3

import os

import argparse
import logging
import re
from html.parser import HTMLParser
import time



TICKTOCK = float()
def tick():
    global TICKTOCK
    TICKTOCK = time.time()

def tock():
    global TICKTOCK
    elapsed = time.time() - TICKTOCK
    return elapsed

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
            regex = '|'.join(pattern_list) if pattern_list else attr_dict['pattern']
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
                regex = r"[\{\[]([ \w].+?)[\}\]]\(?(" + pair[1] + r")\)?"
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

def main():
    tick()
    parser = argparse.ArgumentParser()
    parser.add_argument("-dd", "--debug", "-vv", "--verbose",
                        action="store_true", help="debug mode")
    parser.add_argument("-d", "--info", "-v",
                        action="store_true", help="debug mode")
    parser.add_argument("-i", "--ignore", nargs='+', type=str,
                        help="space separated list of files to be ignored",
                        default=list())
    args = parser.parse_args()

    logger = logging.getLogger('journal_tagger')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)
    if args.info:
        logger.setLevel(logging.INFO)
    elif args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    git_integration_branch = "small_feature"
    git_md_branch = "small_feature_md"
    git_web_branch = "small_feature_web"
    whitelist = [
        ".gitignore",
        "local",
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
    logger.info("main: List of files: %s", str(files))
    logger.info("initialization time: {:.5f}sec".format(tock()))

    tick()
    tag_retriever = TagParser()
    # pass 1 - generate tags
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as file_stream:
            tag_retriever.feed(file_stream.read())

    logger.info("Tag count: %s", str(len(tag_retriever.tags)))
    # pass 2 - use tags to create links
    write_time = 0.0
    logger.info("tag lookup time: {:.5f}sec".format(tock()))

    if 'CI' in os.environ and \
            os.environ['TRAVIS_BRANCH'] == git_integration_branch:
        os.system('git remote rm origin')
        os.system('git remote add origin '\
                  'https://${github_user}:${github_token}@github.com/'\
                  '${TRAVIS_REPO_SLUG}.git > /dev/null 2>&1')
        os.system('git config --global user.email "travis@travis-ci.org"')
        os.system('git config --global user.name "Travis CI"')
        os.system('git fetch')
        os.system('git checkout ' + git_integration_branch)

    for file_path in files:
        text = None
        logger.warning(file_path)
        with open(file_path, 'r', encoding='utf-8') as file_stream:
            tick()
            text = file_stream.read()
            tagger = TagCreator(tag_retriever.tags)
            tagger.feed(text)
            logger.debug("processing time: {:.5f}sec".format(tock()))
            write_time += tock()
            tagger.close()
            text = tagger.text
        if 'CI' not in os.environ:
            file_path = "local/" + file_path
        with open(file_path, 'w', encoding='utf-8') as file_stream:
            file_stream.write(text)

    if 'CI' in os.environ and \
            os.environ['TRAVIS_BRANCH'] == git_integration_branch:
        os.system('git commit -am "Tags processed: '
                  + os.environ['TRAVIS_COMMIT_MESSAGE'] + '"')
        os.system('git push -f origin ' + git_integration_branch + ':'
                  + git_md_branch + ' --quiet')
    logger.info("tag writing time: {:.5f}sec".format(write_time))

if __name__ == "__main__":
    main()
