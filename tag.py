#!/usr/bin/env python3

import os
import sys
import re
from html.parser import HTMLParser



fileList = [f for f in os.listdir() if os.path.isfile(f)]
tags = []

class myParser(HTMLParser):
  def handle_starttag(self, tag, attrs):
    if 'id' not in dict(attrs).keys():
      return
    if tag == "a" and re.match(r"._.+", dict(attrs)['id']):
      if 'class' not in dict(attrs).keys():
        return
      for alias in dict(attrs)['class'].split(','):
        alias = r" ("+alias.replace(r"*", r"\w{4}")+r") "
        global tags
        tags.append([alias, dict(attrs)['id']])
        
whitelist = [
  sys.argv[0][2:],
  ".gitignore"
  "requirements.txt",
  ".travis.yml",
  "test.py",
  "tag.py"
  ]

feedback = ""

def write(text):
  global feedback
  feedback += text + "\n"

tagRetreiver = myParser()
# pass 1 - generate tags
for filePath in fileList:
  if filePath in whitelist:
    continue
  with open(filePath, 'r', encoding='utf-8') as fileStream:
    tagRetreiver.feed(fileStream.read())

# pass 2 - use tags to create links
for filePath in fileList:
  if filePath in whitelist:
    continue
  text = None
  with open(filePath, 'r', encoding='utf-8') as fileStream:
    text = fileStream.read()
    for pair in tags:
      print (pair[0]+ " " + pair[1])
      text = re.sub(pair[0], r"[\1](#"+pair[1]+")", text)
  with open(filePath, 'w', encoding='utf-8') as fileStream:
    fileStream.write(text)
    
    
if feedback != "":
  print(feedback)
  sys.exit(1)
else:
  print("Test passed!")
  sys.exit(0)