#!/usr/bin/env python3

import os
import sys
import re
from html.parser import HTMLParser



fileList = [f for f in os.listdir() if os.path.isfile(f)]
tags = []

class myParser(HTMLParser):
  def handle_starttag(self, tag, attrs):
    if tag != "a":
      return
    if 'href' in attrDict.keys():
      return
    attrDict = dict(attrs)
    if 'id' not in attrDict.keys():
      return
    if   'pattern' in attrDict.keys():
      patternList = attrDict['pattern'].split(',').sort(key = len)
      regex = '|'.join(patternList)
      regex = regex.replace(r"*", r"\w{0,4}")
      global tags
      tags.append([attrDict['id'], regex])
    elif 'regex'   in attrDict.keys():
      global tags
      tags.append([attrDict['id'], attrDict['regex']])
    else:
      return

        
whitelist = [
  sys.argv[0][2:],
  ".gitignore"
  "requirements.txt",
  ".travis.yml",
  "test.py",
  "tag.py"
  ]

tagRetreiver = myParser()
# pass 1 - generate tags
for filePath in fileList:
  if filePath in whitelist:
    continue
  with open(filePath, 'r', encoding='utf-8') as fileStream:
    tagRetreiver.feed(fileStream.read())

#print (tags)
# pass 2 - use tags to create links
for filePath in fileList:
  if filePath in whitelist2:
    continue
  text = None
  with open(filePath, 'r', encoding='utf-8') as fileStream:
    text = fileStream.read()
    for pair in tags:
      #all user-tags `[whatever](Actual Name)`
      regex = r"(\[[ \w].+?\]\()" + r"("+pair[1]+r")" + r"(\))"
      substitute = r"\1#"+pair[0]+r"\3"
      text = re.sub(regex, substitute, text)
      
      #all standard tags unless it is already tagged [] or in between ><
      regex = r"([^[^>])" + r"("+pair[1]+r")" + r"([^]^<])"
      substitute = r"\1(#"+pair[0]+r")\3"
      text = re.sub(regex, substitute, text)
  with open(filePath, 'w', encoding='utf-8') as fileStream:
    fileStream.write(text)
    
    
if feedback != "":
  print(feedback)
  sys.exit(1)
else:
  print("Test passed!")
  sys.exit(0)