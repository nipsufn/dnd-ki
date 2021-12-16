#!/usr/bin/env python3
"""
This script creates cross-referencing tags in md files
"""
import os
import sys
import argparse
import logging
import re
from multiprocessing import Pool

from classes.console import Console
from classes.ticktock import TickTock
from classes.tag_creator import TagCreator
from classes.tag_parser import TagParser
from classes.gha import GHA

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
    files = sorted(files, key = lambda x: os.stat(x).st_size, reverse = True)
    logger.trace("List of files: %s", str(files))
    return files

def process_tags_in_file(file_path, logger, prefix, tags):
    text = None
    #logger.trace(file_path)
    with open(file_path, 'r', encoding='utf-8') as file_stream:
        TickTock.tick()
        text = file_stream.read()
        tagger = TagCreator(tags)
        tagger.feed(text)
        logger.trace("{} processing time: {:.5f}sec".format(file_path, TickTock.tock()))
        write_time = TickTock.tock()
        tagger.close()
        text = tagger.text
    # pull pair id + textblock from tag_retriever object
    file_path = prefix + file_path
    with open(file_path, 'w', encoding='utf-8') as file_stream:
        file_stream.write(text)
    return write_time

def process_tags(files, logger, prefix=""):
    TickTock.tick()
    tag_retriever = TagParser(logger)
    # pass 1 - generate tags
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as file_stream:
            tag_retriever.feed(file_stream.read())

    logger.debug("Tag count: %s", str(len(tag_retriever.tags)))
    # pass 2 - use tags to create links
    write_time = 0.0
    logger.info("Tag lookup time: {:.5f}sec".format(TickTock.tock()))
    TickTock.tick()
    with Pool(processes=16) as thread_pool:
        threads = []
        for file_path in files:
            logger.trace("file process added to pool: {}".format(file_path))
            threads.append(thread_pool.apply_async(process_tags_in_file, (file_path, logger, prefix, tag_retriever.tags,)))
        for thread in threads:
            write_time += thread.get()
    logger.info("tag writing sum time: {:.5f}sec".format(write_time))
    logger.info("Tag writing real time: {:.5f}sec".format(TickTock.tock()))

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
        ".github",
        "local",
        "requirements.txt",
        ".GHA.yml",
        ".vscode"
        "test.py",
        "tag.py",
        ".vimrc",
        "tag_old.py",
        "tag_mid.py"
        ]

    # code
    logger = prepare_logger(args)
    files = prepare_files(args, whitelist, logger)
    logger.info("Initialization time: {:.5f}sec".format(TickTock.tock()))
    feedback = test_files(files)
    # comment test result on source repo and bail if needed
    GHA.git_setup()
    GHA.git_comment(feedback)
    if feedback != "Test passed!":
        for line in feedback.splitlines():
            logger.error(line)
        sys.exit(1)
    prefix = "local/"
    commit_message = ""
    if 'CI' in os.environ:
        prefix = "dnd-ki/"
        commit_message = GHA.git_get_commit()
        GHA.git_clone('nipsufn/dnd-ki')
    process_tags(files, logger, prefix)
    feedback = test_files(files, prefix)
    if feedback != "Test passed!":
        if 'CI' in os.environ:
            GHA.git_comment('Parsing failed: ' + feedback)
        for line in feedback.splitlines():
            logger.error(line)
        sys.exit(1)
    else:
        if 'CI' in os.environ:
            GHA.git_dir = os.environ['PWD'] + '/' + prefix
            # GHA.git_setup()
            GHA.git_add('*.md')
            GHA.git_commit_all('Parsed: ' + commit_message)
            GHA.git_unbork_gha_root('nipsufn/dnd-ki')
            commit = GHA.git_push()
            GHA.git_comment(feedback, commit, 'nipsufn/dnd-ki')
        else:
            logger.info(feedback)
        sys.exit(0)

if __name__ == "__main__":
    main()
