#!/usr/bin/env python3

import os
import sys
import re
from html.parser import HTMLParser



fileList = [f for f in os.listdir() if os.path.isfile(f)]

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
    if len(self.curentHtmlTag) == 0 or self.curentHtmlTag[0] != "a":
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
    
whitelist = [
  sys.argv[0][2:],
  ".gitignore",
  "requirements.txt",
  ".travis.yml",
  "test.py",
  "tag.py"
  ]
  
tagRetreiver = tagParser()
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
  print (filePath)
  with open(filePath, 'r', encoding='utf-8') as fileStream:
    text = fileStream.read()
    tagger = tagCreator(tagRetreiver.tags)
    tagger.feed(text)
    tagger.close()
    text = tagger.text
    del tagger

  with open(filePath, 'w', encoding='utf-8') as fileStream:
    fileStream.write(text)
    
 