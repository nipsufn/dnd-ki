#!/usr/bin/env python3
"""
This script creates cross-referencing tags in md files
"""
import os
import sys
import argparse
import logging
from multiprocessing import Pool, cpu_count

from classes.tag_creator import TagCreator
from classes.tag_parser import TagParser
import classes.gha as GHA
from classes.test import Test

def prepare_logger(args):
    """create global logger, add trace loglevel"""
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
    elif args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger

def prepare_files(args, whitelist, logger):
    """read directory to create file list, exclude some and sort by size"""
    whitelist.extend(args.ignore)
    with open(".gitignore", 'r', encoding='utf-8') as gitignore:
        whitelist.extend(gitignore.read().splitlines())
    logger.debug('Ignored files: %s', whitelist)
    files = [f for f in os.listdir() if os.path.isfile(f)]
    files = list(set(files) - set(whitelist))
    files = sorted(files, key = lambda x: os.stat(x).st_size, reverse = True)
    logger.debug('List of files: %s', files)
    return files

def parse_tags_in_file(file_path, logger):
    """wrap parsing files for tags - multiprocess"""
    tag_retriever = TagParser(logger)
    with open(file_path, 'r', encoding='utf-8') as file_stream:
        tag_retriever.feed(file_stream.read())
    return tag_retriever.tags

def create_tags_in_file(file_path, logger, prefix, tags):
    """wrap creating tags in files - multiprocess"""
    text = None
    with open(file_path, 'r', encoding='utf-8') as file_stream:
        text = file_stream.read()
        tagger = TagCreator(tags, logger)
        tagger.feed(text)
        tagger.close()
        text = tagger.text
    file_path = prefix + file_path
    with open(file_path, 'w', encoding='utf-8') as file_stream:
        file_stream.write(text)

def process_tags(files, logger, prefix=""):
    """process tags - find anchors and fix references"""
    logger.debug('CPU Core count: %d', cpu_count())
    thread_no = cpu_count()
    # pass 1 - generate tags
    tags = []
    with Pool(processes=thread_no) as thread_pool:
        threads = []
        for file_path in files:
            logger.debug('Tag parse process added to pool for file: %s', file_path)
            threads.append(thread_pool.apply_async(parse_tags_in_file, (file_path, logger,)))
        for thread in threads:
            tags.extend(thread.get())

    logger.debug('Tag count: %d', len(tags))
    # pass 2 - use tags to create links
    with Pool(processes=thread_no) as thread_pool:
        threads = []
        for file_path in files:
            logger.debug('Tag create process added to pool for file: %s', file_path)
            threads.append(
                thread_pool.apply_async(
                    create_tags_in_file, (file_path, logger, prefix, tags,)))
        for thread in threads:
            thread.get()

def main():
    """wrap main for entrypoint"""
    # argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-dd", "--trace", "-vv",
                        action="store_true", help="debug mode")
    parser.add_argument("-d", "--debug", "-v", "--verbose",
                        action="store_true", help="debug mode")
    parser.add_argument("-i", "--ignore", nargs='+', type=str,
                        help="space separated list of files to be ignored",
                        default=[])
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
        "tag_singlethread.py",
        "tag_singlethread.prof",
        ".vimrc",
        ".DS_Store"
        ]

    # code
    logger = prepare_logger(args)
    files = prepare_files(args, whitelist, logger)
    feedback = Test(files).get_feedback()
    if feedback != "Test passed!":
        if 'CI' in os.environ:
            GHA.git_comment('Parsing failed: ' + feedback)
        for line in feedback.splitlines():
            logger.error(line)
        sys.exit(1)
    prefix = "local/"
    if 'CI' in os.environ:
        prefix = "parsed/"
    process_tags(files, logger, prefix)
    feedback = Test(files, prefix).get_feedback()
    if feedback != "Test passed!":
        if 'CI' in os.environ:
            GHA.git_comment('Parsing failed: ' + feedback)
        for line in feedback.splitlines():
            logger.error(line)
        sys.exit(1)
    logger.info(feedback)
    sys.exit(0)

if __name__ == "__main__":
    main()
