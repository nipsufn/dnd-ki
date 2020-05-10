#!/usr/bin/env python3

import os
import sys

import argparse
import logging
import re
from html.parser import HTMLParser
import time

logger = logging.getLogger('journal_tagger')

ticktock = float()
def tick():
  global ticktock
  ticktock = time.time()

def tock():
  global ticktock
  elapsed = time.time() - ticktock
  return elapsed

class tagParser(HTMLParser):
  def __init__(self):
    self.tags = []
    super().__init__()
    
  def handle_starttag(self, tag, attrs):
    if tag != "a":
      return
    attrDict = dict(attrs)
    if 'href' in attrDict.keys():
      return
    if 'id' not in attrDict.keys():
      return
    if   'pattern' in attrDict.keys():
      patternList = sorted(attrDict['pattern'].split(','), key=len, reverse=True)
      regex = '|'.join(patternList) if patternList else attrDict['pattern']
      regex = regex.replace(r"*", r"\w{0,7}")
      
      self.tags.append([attrDict['id'], regex])
    elif 'regex'   in attrDict.keys():
      
      self.tags.append([attrDict['id'], attrDict['regex']])
    else:
      return

class tagCreator(HTMLParser):
  def __init__(self, tags):
    self.curentHtmlTag = []
    self.tags = tags
    self.text = ""
    super().__init__()
  
  def handle_starttag(self, tag, attrs):
    self.curentHtmlTag.append(tag)
    self.text += self.get_starttag_text()

  def handle_endtag(self, tag):
    if len(self.curentHtmlTag) == 0 or self.curentHtmlTag[0] == tag:
      self.curentHtmlTag.pop()
    if tag == "br":
      return
    self.text += "</" + tag + ">"

  def handle_data(self, data):
    if len(self.curentHtmlTag) == 0:
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

def main():
  tick()
  parser = argparse.ArgumentParser()
  parser.add_argument("-dd", "--debug", "-vv", "--verbose", action="store_true",
                      help="debug mode")
  parser.add_argument("-d", "--info", "-v", action="store_true",
                      help="debug mode")
  parser.add_argument("-i", "--ignore", nargs='+', type=str,
                      help="space separated list of files to be ignored",
                      default=list())
  args = parser.parse_args()

  global logger
  log_handler = logging.StreamHandler()
  log_handler.setFormatter(
      logging.Formatter(
          '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
          )
      )
  logger.addHandler(log_handler)
  if args.info:
    logger.setLevel(logging.INFO)
  elif args.debug:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.WARNING)

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
  tagRetreiver = tagParser()
  # pass 1 - generate tags
  for filePath in files:
    with open(filePath, 'r', encoding='utf-8') as fileStream:
      tagRetreiver.feed(fileStream.read())

  logger.info("Tag count: " + str(len(tagRetreiver.tags)))
  # pass 2 - use tags to create links
  write_time = 0.0
  logger.info("tag lookup time: {:.5f}sec".format(tock()))
  if 'CI' in os.environ and os.environ['TRAVIS_BRANCH'] == "small_feature":
    os.system('git config --global user.email "travis@travis-ci.org"')
    os.system('git config --global user.name "Travis CI"')
    os.system('git fetch')
    os.system('git checkout small_feature_md')

  for filePath in files:
    text = None
    logger.warning(filePath)
    with open(filePath, 'r', encoding='utf-8') as fileStream:
      tick()
      text = fileStream.read()
      tagger = tagCreator(tagRetreiver.tags)
      tagger.feed(text)
      logger.debug("processing time: {:.5f}sec".format(tock()))
      write_time += tock()
      tagger.close()
      text = tagger.text
    if 'CI' not in os.environ:
      filePath = "local/" + filePath
    with open(filePath, 'w', encoding='utf-8') as fileStream:
      fileStream.write(text)

  if 'CI' in os.environ and os.environ['TRAVIS_BRANCH'] == "small_feature":
      os.system('git commit -am "$TRAVIS_COMMIT_MESSAGE"')
      os.system('git remote rm origin')
      os.system('git remote add origin https://${github_user}:${github_token}@github.com/${TRAVIS_REPO_SLUG}.git > /dev/null 2>&1')
      os.system('git push origin master --quiet')
  logger.info("tag writing time: {:.5f}sec".format(write_time))

if __name__ == "__main__":
  main()
 