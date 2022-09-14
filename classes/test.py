# test.py
"""Helper module for repo operations inside GHA CI environment
"""
import re
import logging
from tokenize import String

class Test:
    """count characters that should be in pairs"""
    def __detect_balance(self, balance: dict, line: String) -> None:
        balance['"'] += line.count('"')
        balance['<'] += line.count('<')
        balance['>'] += line.count('>')
        balance['('] += line.count('(')
        balance[')'] += line.count(')')
        balance['['] += line.count('[')
        balance[']'] += line.count(']')

        if re.search(r"\(\?<!", line):
            balance['<'] -= 1
        if re.match(r"^(\t| )*>", line):
            balance['>'] -= 1

    def __detect_merge_conflict(self, line_text) -> bool:
        """check if line contains merge conflict"""
        if re.match(r"[<>=]{7}", line_text):
            return True
        return False

    def __parse_tags_and_refs(self , line, match, file_path) -> None:
        """detect tags/references that do not match format while extracting them"""
        line_text = line[1]
        line_no = line[0]
        if re.search(r"<a id='[a-zA-Z0-9](_[a-zA-Z0-9]+?)+?'",
                        line_text[match.start(0)-7:match.end(0)+6]):
            self.__tags.append({"tag": match.group(0), "line": line_no,
                            "position": match.start(0), "path": file_path})
        elif re.search(r"<a id=\"[a-zA-Z0-9](_[a-zA-Z0-9]+?)+?\"",
                        line_text[match.start(0)-7:match.end(0)+6]):
            self.__tags.append({"tag": match.group(0), "line": line_no,
                            "position": match.start(0), "path": file_path})
        elif re.search(
                r"\[[^\[^\]]+?\]\(#[a-zA-Z0-9](_[a-zA-Z0-9]+)+\)",
                line_text[0:match.end(0)+1]):
            self.__refs.append({"tag": match.group(0), "line": line_no,
                            "position": match.start(0), "path": file_path,
                            "ok": False})
        elif re.search(r'<a href="[^"]+?(_[a-zA-Z0-9]+)+">.+?</a>',
                        line_text):
            return
        elif re.search(r"\[[^\[^\]]+?\]\(http.+?\)",
                        line_text[0:match.end(0)+1]):
            return
        else:
            self.__feedback += ("Tag or reference malformed: "
                        + match.group(0)
                        + "; line: " + str(line_no+1)
                        + "; position: " + str(match.start(0))
                        + "; file: " + file_path + "\n")

    def __check_balance(self, balance, file_path) -> None:
        """describe balance"""
        if balance['"']%2 != 0:
            self.__feedback += "Unmatched \" in file: " + file_path + "\n"
        if balance['<'] != balance['>']:
            self.__feedback += "Unmatched <> in file: " + file_path + "\n"
        if balance['('] != balance[')']:
            self.__feedback += "Unmatched () in file: " + file_path + "\n"
        if balance['['] != balance[']']:
            self.__feedback += "Unmatched [] in file: " + file_path + "\n"

    def __check_merge_conflict(self, merge_conflict, file_path) -> String:
        """describe merge conflict"""
        if merge_conflict:
            self.__feedback += "Merge conflict in file: " + file_path + "\n"

    def __validate_brackets_and_format(self, files, prefix) -> None:
        """validate brackets and tag/ref format"""
        for file_path in files:
            with open(prefix + file_path, 'r', encoding='utf-8') as file_stream:
                self.__logger.trace("file opened: " + file_path)
                balance = dict.fromkeys(['"','<','>','(',')','[',']'], 0)
                merge_conflict = False
                for line in enumerate(file_stream):
                    self.__detect_balance(balance, line[1])

                    merge_conflict = self.__detect_merge_conflict(line[1])

                    for match in re.finditer(r"[a-zA-Z0-9](_[a-zA-Z0-9]+)+",
                                            line[1]):
                        self.__parse_tags_and_refs(line, match, file_path)

                self.__check_balance(balance, file_path)
                self.__check_merge_conflict(merge_conflict, file_path)

    def __validate_tags(self) -> None:
        """validate tags"""
        for outer in enumerate(self.__tags):
            for inner in enumerate(self.__tags):
                if inner[0] > outer[0] and outer[1]["tag"] == inner[1]["tag"]:
                    self.__feedback += ("Duplicate tag found: " + inner[1]["tag"]
                                + "; first: line: " + str(outer[1]["line"]+1)
                                + ", position: " + str(outer[1]["position"])
                                + ", file: " + outer[1]["path"]
                                + "; subsequent: line: " + str(inner[1]["line"]+1)
                                + ", position: " + str(inner[1]["position"])
                                + ", file: " + inner[1]["path"]
                                + "\n")

    def __validate_refs(self) -> None:
        """validate refs"""
        for ref in self.__refs:
            for tag in self.__tags:
                if ref["tag"] == tag["tag"]:
                    ref["ok"] = True
            if not ref["ok"]:
                self.__feedback += ("Reference malformed: " + ref["tag"]
                            + "; line: " + str(ref["line"]+1)
                            + "; position: " + str(ref["position"])
                            + "; file: " + ref["path"]
                            + "\n")

    def __init__(self, files, prefix=""):
        """
        validate files against:
        - unbalanced brackets, quotes etc.
        - duplicate tags
        - tags that do not conform to format
        - refs that do not conform to format
        """
        self.__logger = logging.getLogger(type(self).__name__)

        self.__feedback = ""
        self.__prefix = prefix
        self.__files = files
        self.__tags = []
        self.__refs = []
        self.__validate_brackets_and_format(files, prefix)
        self.__validate_tags()
        self.__validate_refs()

    def get_feedback(self):
        """get feedback"""
        if not self.__feedback:
            return "Test passed!"
        return self.__feedback

    def rerun(self):
        """run tests again on the same set of files"""
        self.__validate_brackets_and_format(self.__files, self.__prefix)
        self.__validate_tags()
        self.__validate_refs()
