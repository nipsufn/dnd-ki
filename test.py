#!/usr/bin/env python3

import os
import sys
import re
import requests

fileList = [f for f in os.listdir() if os.path.isfile(f)]
tags = []
refs = []

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


for filePath in fileList:
  if filePath in whitelist:
    continue
  with open(filePath, 'r', encoding='utf-8') as fileStream:
    balance = [0 for x in range(7)]
    mergeConflict = False
    for lineNo, lineText in enumerate(fileStream):
      balance[0] += lineText.count('"')
      balance[1] += lineText.count('<')
      balance[2] += lineText.count('>')
      balance[3] += lineText.count('(')
      balance[4] += lineText.count(')')
      balance[5] += lineText.count('[')
      balance[6] += lineText.count(']')
      if re.match(r"[<>=]{7}", lineText):
        mergeConflict = True
      for match in re.finditer(r"[a-zA-Z0-9](_[a-zA-Z0-9]+)+", lineText):
        if re.search(r"<a id='[a-zA-Z0-9](_[a-zA-Z0-9]+?)+?'", lineText[match.start(0)-7:match.end(0)+6]):
          tags.append([match.group(0), lineNo, match.start(0), filePath])
        elif re.search(r"<a id=\"[a-zA-Z0-9](_[a-zA-Z0-9]+?)+?\"", lineText[match.start(0)-7:match.end(0)+6]):
          tags.append([match.group(0), lineNo, match.start(0), filePath])
        elif re.search(r"\[[^\[^\]]+?\]\(#[a-zA-Z0-9](_[a-zA-Z0-9]+)+\)", lineText[0:match.end(0)+1]):
          refs.append([match.group(0), lineNo, match.start(0), filePath, False])
        elif re.search(r'<a href="[^"]+?(_[a-zA-Z0-9]+)+">.+?</a>', lineText):
          continue
        else:
          write("Tag or reference malformed: " + match.group(0)
            + "; line: " + str(lineNo+1)
            + "; position: " + str(match.start(0))
            + "; file: " + filePath
            )
    if balance[0]%2 != 0:
      write("Unmatched \" in file: " + filePath)
    if balance[1] != balance[2]:
      write("Unmatched <> in file: " + filePath)
    if balance[3] != balance[4]:
      write("Unmatched () in file: " + filePath)
    if balance[5] != balance[6]:
      write("Unmatched [] in file: " + filePath)
    if mergeConflict:
      write("Merge conflict in file: " + filePath)

for n, x in enumerate(tags):
  for o, y in enumerate(tags):
    if o > n and x[0] == y[0]:
      write("Duplicate tag found: " + y[0]
        + "; first: line: " + str(x[1]+1)
        + ", position: " + str(x[2])
        + ", file: " + x[3]
        + "; subsequent: line: " + str(y[1]+1)
        + ", position: " + str(y[2])
        + ", file: " + y[3]
        )

for ref in refs:
  for tag in tags:
    if ref[0] == tag[0]:
      ref[4] = True
  if not ref[4]:
    write("Reference malformed: " + ref[0]
      + "; line: " + str(ref[1]+1)
      + "; position: " + str(ref[2])
      + "; file: " + ref[3]
      )

if 'CI' in os.environ:
  if feedback != "":
    r = requests.post('https://api.github.com/repos/'+os.environ['TRAVIS_REPO_SLUG']+'/commits/'+os.environ['TRAVIS_COMMIT']+'/comments',
      json={"body": feedback},
      auth=requests.auth.HTTPBasicAuth(os.environ['github_user'], os.environ['github_token'])
      )
  else:
    r = requests.post('https://api.github.com/repos/'+os.environ['TRAVIS_REPO_SLUG']+'/commits/'+os.environ['TRAVIS_COMMIT']+'/comments',
      json={"body": "Test passed!"},
      auth=requests.auth.HTTPBasicAuth(os.environ['github_user'], os.environ['github_token'])
      )

if feedback != "":
  print(feedback)
  sys.exit(1)
else:
  print("Test passed!")
  sys.exit(0)