#!/usr/bin/python3

import os
import sys
import re

fileList = [f for f in os.listdir() if os.path.isfile(f)]
tags = []
refs = []

for filePath in fileList:
  if filePath == sys.argv[0][2:]:
    continue
  with open(filePath, 'r', encoding='utf-8') as fileStream:
    balance = [0 for x in range(7)]
    for lineNo, lineText in enumerate(fileStream):
      balance[0] += lineText.count('"')
      balance[1] += lineText.count('<')
      balance[2] += lineText.count('>')
      balance[3] += lineText.count('(')
      balance[4] += lineText.count(')')
      balance[5] += lineText.count('[')
      balance[6] += lineText.count(']')
      for match in re.finditer(r"\w(_\w+)+", lineText):
        if re.search(r"<a id='\w(_\w+)+'></a>", lineText[match.start(0)-7:match.end(0)+6]):
          tags.append([match.group(0), lineNo, match.start(0), filePath])
        elif re.search(r"<a id=\"\w(_\w+)+\"></a>", lineText[match.start(0)-7:match.end(0)+6]):
          tags.append([match.group(0), lineNo, match.start(0), filePath])
        elif re.search(r"\[[^\[^\]]+?\]\(#\w(_\w+)+\)", lineText[0:match.end(0)+1]):
          refs.append([match.group(0), lineNo, match.start(0), filePath, False])
        else:
          print("Tag or reference malformed: " + match.group(0)
            + "; line: " + str(lineNo+1)
            + "; position: " + str(match.start(0))
            + "; file: " + filePath
            )
    if balance[0]%2 != 0:
      print("Unmatched \" in file: " + filePath)
    if balance[1] != balance[2]:
      print("Unmatched <> in file: " + filePath)
    if balance[3] != balance[4]:
      print("Unmatched () in file: " + filePath)
    if balance[5] != balance[6]:
      print("Unmatched [] in file: " + filePath)

for n, x in enumerate(tags):
  for o, y in enumerate(tags):
    if o > n and x[0] == y[0]:
      print("Duplicate tag found: " + y[0]
        + "; first: line: " + str(x[1]+1)
        + ", position: " + str(x[2])
        + ", file: " + x[3]
        + "; subsequent: line: " + str(y[1]+1)
        + ", position: " + str(y[2])
        + ", file: " + y[3])

for n, x in enumerate(refs):
  for o, y in enumerate(tags):
    if x[0] == y[0]:
      x[4] = True

for ref in refs:
  if not ref[4]:
    print("Reference malformed: " + ref[0]
      + "; line: " + str(ref[1]+1)
      + "; position: " + str(ref[2])
      + "; file: " + ref[3]
      )
