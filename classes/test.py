# test.py
"""Helper module for repo operations inside GHA CI environment
"""
import re
import logging
from tokenize import String

class Test:
    """Test journal files"""
    __logger = None
    @staticmethod
    def __init__(loglevel=logging.WARN):
        """constructor, set up logging including extra loglevel"""
        logging.TRACE = 5
        logging.addLevelName(5, "TRACE")
        Test.__logger = logging.getLogger('test')
        setattr(Test.__logger, 'trace',
                lambda *args: Test.__logger.log(5, *args))

        log_handler = logging.StreamHandler()
        log_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        Test.__logger.addHandler(log_handler)
        Test.__logger.setLevel(loglevel)

    @staticmethod
    def __detect_regex_negative_lookbehind(line_text) -> int:
        """check if line contains lookbehind"""
        if re.search(r"\(\?<!", line_text):
            return -1
        return 0

    @staticmethod
    def __detect_merge_conflict(line_text) -> bool:
        """check if line contains merge conflict"""
        if re.match(r"[<>=]{7}", line_text):
            return True
        return False

    @staticmethod
    def __detect_blockquotes(line_text) -> int:
        """check if line contains blockquote"""
        if re.match(r"^(\t| )*>", line_text):
            return -1
        return 0

    @staticmethod
    def __detect_malformed_tag(tags, refs, line, match, file_path) -> String:
        """detect tags/references that do not match format while extracting them"""
        line_text = line[1]
        line_no = line[0]
        if re.search(r"<a id='[a-zA-Z0-9](_[a-zA-Z0-9]+?)+?'",
                        line_text[match.start(0)-7:match.end(0)+6]):
            tags.append([match.group(0), line_no, match.start(0),
                            file_path])
        elif re.search(r"<a id=\"[a-zA-Z0-9](_[a-zA-Z0-9]+?)+?\"",
                        line_text[match.start(0)-7:match.end(0)+6]):
            tags.append([match.group(0), line_no, match.start(0),
                            file_path])
        elif re.search(
                r"\[[^\[^\]]+?\]\(#[a-zA-Z0-9](_[a-zA-Z0-9]+)+\)",
                line_text[0:match.end(0)+1]):
            refs.append([match.group(0), line_no, match.start(0),
                            file_path, False])
        elif re.search(r'<a href="[^"]+?(_[a-zA-Z0-9]+)+">.+?</a>',
                        line_text):
            return ""
        elif re.search(r"\[[^\[^\]]+?\]\(http.+?\)",
                        line_text[0:match.end(0)+1]):
            return ""
        else:
            return ("Tag or reference malformed: "
                        + match.group(0)
                        + "; line: " + str(line_no+1)
                        + "; position: " + str(match.start(0))
                        + "; file: " + file_path + "\n")
        return ""

    @staticmethod
    def __check_balance(balance, file_path) -> String:
        """describe balance"""
        if balance['"']%2 != 0:
            return "Unmatched \" in file: " + file_path + "\n"
        if balance['<'] != balance['>']:
            return "Unmatched <> in file: " + file_path + "\n"
        if balance['('] != balance[')']:
            return "Unmatched () in file: " + file_path + "\n"
        if balance['['] != balance[']']:
            return "Unmatched [] in file: " + file_path + "\n"
        return ""

    @staticmethod
    def __check_merge_conflict(merge_conflict, file_path) -> String:
        """describe merge conflict"""
        if merge_conflict:
            return "Merge conflict in file: " + file_path + "\n"
        return ""

    @staticmethod
    def __validate_brackets_and_format(files, prefix):
        """validate brackets and tag/ref format"""
        tags = []
        refs = []
        feedback = ""
        for file_path in files:
            with open(prefix + file_path, 'r', encoding='utf-8') as file_stream:
                balance = dict.fromkeys(['"','<','>','(',')','[',']'], 0)
                merge_conflict = False
                for line in enumerate(file_stream):
                    balance['"'] += line[1].count('"')
                    balance['<'] += line[1].count('<')
                    balance['>'] += line[1].count('>')
                    balance['('] += line[1].count('(')
                    balance[')'] += line[1].count(')')
                    balance['['] += line[1].count('[')
                    balance[']'] += line[1].count(']')

                    balance['<'] += Test.__detect_regex_negative_lookbehind(line[1])
                    merge_conflict = Test.__detect_merge_conflict(line[1])
                    balance['>'] += Test.__detect_blockquotes(line[1])

                    for match in re.finditer(r"[a-zA-Z0-9](_[a-zA-Z0-9]+)+",
                                            line[1]):
                        feedback += Test.__detect_malformed_tag(tags, refs, line,
                            match, file_path)

                feedback += Test.__check_balance(balance, file_path)
                feedback += Test.__check_merge_conflict(merge_conflict, file_path)
        return (tags, refs, feedback)

    @staticmethod
    def __validate_tags_and_refs(tags, refs, feedback):
        """validate tags/refs"""
        for outer in enumerate(tags):
            for inner in enumerate(tags):
                if inner[0] > outer[0] and outer[1][0] == inner[1][0]:
                    feedback += ("Duplicate tag found: " + inner[1][0]
                                + "; first: line: " + str(outer[1][1]+1)
                                + ", position: " + str(outer[1][2])
                                + ", file: " + outer[1][3]
                                + "; subsequent: line: " + str(inner[1][1]+1)
                                + ", position: " + str(inner[1][2])
                                + ", file: " + inner[1][3]
                                + "\n")

        for ref in refs:
            for tag in tags:
                if ref[0] == tag[0]:
                    ref[4] = True
            if not ref[4]:
                feedback += ("Reference malformed: " + ref[0]
                            + "; line: " + str(ref[1]+1)
                            + "; position: " + str(ref[2])
                            + "; file: " + ref[3]
                            + "\n")

        return feedback

    @staticmethod
    def test_files(files, prefix=""):
        """
        validate files against:
        - unbalanced brackets, quotes etc.
        - duplicate tags
        - tags that do not conform to format
        - refs that do not conform to format
        """
        (tags, refs, feedback) = Test.__validate_brackets_and_format(files, prefix)
        Test.__validate_tags_and_refs(tags, refs, feedback)

        if not feedback:
            return "Test passed!"
        return feedback

    @staticmethod
    def set_log_level(loglevel):
        """set loglevel
        Args:
            loglevel (int): loglevel to set
        """
        if not Test.__logger:
            Test.__init__()
        Test.__logger.setLevel(loglevel)
