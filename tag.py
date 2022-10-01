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

__logger = logging.getLogger('journal_tagger')

def prepare_logger(args) -> None:
    """create global logger, add trace loglevel"""

    level = logging.WARNING
    level_str_to_int = {
        'critical': logging.CRITICAL,
        'fatal': logging.FATAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }
    if args.loglevel:
        level=level_str_to_int[args.loglevel]
    if args.debug:
        level = logging.DEBUG
    if args.info:
        level = logging.INFO

    logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(processName)s/%(threadName)s - '
        '%(pathname)s:%(lineno)d- %(name)s - %(message)s', level=level)

def prepare_files(args, whitelist, ):
    """read directory to create file list, exclude some and sort by size"""
    whitelist.extend(args.ignore)
    with open(".gitignore", 'r', encoding='utf-8') as gitignore:
        whitelist.extend(gitignore.read().splitlines())
    __logger.info('Ignored files: %s', whitelist)
    files = [f for f in os.listdir() if os.path.isfile(f)]
    files = list(set(files) - set(whitelist))
    files = sorted(files, key = lambda x: os.stat(x).st_size, reverse = True)
    __logger.warning('List of files: %s', files)
    return files

def parse_tags_in_file(file_path, loglevel: int = logging.WARNING):
    """wrap parsing files for tags - multiprocess"""
    tag_retriever = TagParser(loglevel)
    with open(file_path, 'r', encoding='utf-8') as file_stream:
        tag_retriever.feed(file_stream.read())
    return tag_retriever.tags

def create_tags_in_file(file_path, prefix: str, tags: list, loglevel: int = logging.WARNING):
    """wrap creating tags in files - multiprocess"""
    text = None
    with open(file_path, 'r', encoding='utf-8') as file_stream:
        text = file_stream.read()
        tagger = TagCreator(tags, loglevel)
        tagger.feed(text)
        tagger.close()
        text = tagger.text
    file_path = prefix + file_path
    with open(file_path, 'w', encoding='utf-8') as file_stream:
        file_stream.write(text)

def process_tags(files, prefix=""):
    """process tags - find anchors and fix references"""
    __logger.info('CPU Core count: %d', cpu_count())
    thread_no = cpu_count()
    # pass 1 - generate tags
    tags = []
    with Pool(processes=thread_no) as thread_pool:
        threads = []
        for file_path in files:
            __logger.info('Tag parse process added to pool for file: %s', file_path)
            threads.append(
                thread_pool.apply_async(
                    parse_tags_in_file, (file_path, logging.root.level)))
        for thread in threads:
            tags.extend(thread.get())

    __logger.info('Tag count: %d', len(tags))
    # pass 2 - use tags to create links
    with Pool(processes=thread_no) as thread_pool:
        threads = []
        for file_path in files:
            __logger.info('Tag create process added to pool for file: %s', file_path)
            threads.append(
                thread_pool.apply_async(
                    create_tags_in_file, (file_path, prefix, tags, logging.root.level)))
        for thread in threads:
            thread.get()

def main():
    """wrap main for entrypoint"""
    # argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--loglevel", type=str,
                        choices=['critical','error','warning','info','debug'],
                        help="set loglevel")
    parser.add_argument("-dd", "--debug", "-vv",
                        action="store_true", help="print debug messages")
    parser.add_argument("-d", "--info", "-v", "--verbose",
                        action="store_true", help="print info messages")
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
        ".vimrc",
        ".DS_Store"
        ]

    # code
    prepare_logger(args)
    files = prepare_files(args, whitelist)
    feedback = Test(files).get_feedback()
    if feedback != "Test passed!":
        if 'CI' in os.environ:
            GHA.git_comment('Parsing failed: ' + feedback)
        for line in feedback.splitlines():
            __logger.error(line)
        sys.exit(1)
    prefix = "local/"
    if 'CI' in os.environ:
        prefix = "parsed/"

    process_tags(files, prefix)
    feedback = Test(files, prefix).get_feedback()
    if feedback != "Test passed!":
        if 'CI' in os.environ:
            GHA.git_comment('Parsing failed: ' + feedback)
        for line in feedback.splitlines():
            __logger.error(line)
        sys.exit(1)
    __logger.warning(feedback)
    sys.exit(0)

if __name__ == "__main__":
    main()
