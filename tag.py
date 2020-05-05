#!/usr/bin/env python3

import os
import sys

import argparse
import logging
import re
from html.parser import HTMLParser
import datetime

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
    self.count = 0
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
    if len(self.curentHtmlTag) == 0 or self.curentHtmlTag[0] != "a":
      self.count += 1
      for pair in self.tags:
        #all user-tags `[whatever](Actual Name)`
        regex = r"(\[[ \w].+?\]\()" + r"("+pair[1]+r")" + r"(\))"
        substitute = r"\1#"+pair[0]+r"\3"
        data = re.sub(regex, substitute, data)
        
        #all standard tags unless it is already tagged [] or in between ><
        regex = r"([ ,.()])" + r"("+pair[1]+r")" + r"([ ,.()?!:;\"\n])"
        substitute = r"\1[\2](#"+pair[0]+r")\3"
        data = re.sub(regex, substitute, data)
    self.text += data

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-d", "--debug", "-v", "--verbose", action="store_true",
                      help="debug mode")
  parser.add_argument("-i", "--ignore", nargs='+', type=str,
                      help="space separated list of files to be ignored",
                      default=list())
  args = parser.parse_args()

  logger = logging.getLogger('journal_tagger')
  log_handler = logging.StreamHandler()
  log_handler.setFormatter(
      logging.Formatter(
          '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
          )
      )
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

  tagRetreiver = tagParser()
  # pass 1 - generate tags
  for filePath in files:
    with open(filePath, 'r', encoding='utf-8') as fileStream:
      tagRetreiver.feed(fileStream.read())

  logger.debug("Tag count: " + str(len(tagRetreiver.tags)))
  # pass 2 - use tags to create links
  for filePath in files:
    text = None
    logger.info(filePath)
    with open(filePath, 'r', encoding='utf-8') as fileStream:
      start = datetime.datetime.now()
      text = fileStream.read()
      elapsed_time = datetime.datetime.now() - start
      logger.debug("\tread:  " + str(elapsed_time.seconds) + ":" + str(elapsed_time.microseconds) + "sec")

      start = datetime.datetime.now()
      tagger = tagCreator(tagRetreiver.tags)
      elapsed_time = datetime.datetime.now() - start
      logger.debug("\tinit:  " + str(elapsed_time.seconds) + ":" + str(elapsed_time.microseconds) + "sec")

      start = datetime.datetime.now()
      tagger.feed(text)
      elapsed_time = datetime.datetime.now() - start
      logger.debug("\tfeed:  " + str(elapsed_time.seconds) + ":" + str(elapsed_time.microseconds) + "sec")
      logger.debug("\tcount: " + str(tagger.count))
      tagger.close()
      text = tagger.text
      del tagger

    with open(filePath, 'w', encoding='utf-8') as fileStream:
      fileStream.write(text)

if __name__ == "__main__":
  main()
 