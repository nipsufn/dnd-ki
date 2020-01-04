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
    attrDict = dict(attrs)
    if 'href' in attrDict.keys():
      return
    if 'id' not in attrDict.keys():
      return
    global tags
    if   'pattern' in attrDict.keys():
      patternList = sorted(attrDict['pattern'].split(','), key=len, reverse=True)
      regex = '|'.join(patternList) if patternList else attrDict['pattern']
      print (regex)
      regex = regex.replace(r"*", r"\w{0,4}")
      
      tags.append([attrDict['id'], regex])
    elif 'regex'   in attrDict.keys():
      
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
whitelist2 = [
  sys.argv[0][2:],
  ".gitignore"
  "requirements.txt",
  ".travis.yml",
  "test.py",
  "tag.py",
  "bestariusz.md",
  "header.md",
  "heraldyka.md",
  "lokacje.md",
  "ogloszenia.md",
  "postaci-graczy.md",
  "postaci.md",
  "readme.md",
  "requirements.txt",
  "rozne.md",
  "toc.md",
  "zadania.md"
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
      substitute = r"\1[\2](#"+pair[0]+r")\3"
      text = re.sub(regex, substitute, text)
  with open(filePath, 'w', encoding='utf-8') as fileStream:
    fileStream.write(text)
    
 