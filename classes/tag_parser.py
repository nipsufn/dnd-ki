# tag_parser.py
"""Module detecting keywords to be used as tags
"""
import re
from html.parser import HTMLParser

class TagParser(HTMLParser):
    """find HTML anchors and create list of re expressions"""
    __logger = None
    def __init__(self, logger):
        """override parent constructor, set up and then call parent's constructor"""
        self.tags = []
        self.descriptions = []
        self.__logger = logger
        super().__init__()

    def handle_starttag(self, tag, attrs):
        """override partent method - assemble list of id, regex 1 and regex 2"""
        #self.__logger.trace("tag  %s", tag)
        if tag != "a":
            return
        attr_dict = dict(attrs)
        if 'href' in attr_dict.keys():
            return
        if 'id' not in attr_dict.keys():
            return
        if 'pattern' in attr_dict.keys():
            pattern_list = sorted(attr_dict['pattern'].split(','), key=len,
                                  reverse=True)
            regex = '|'.join(pattern_list) if pattern_list \
                else attr_dict['pattern']
            regex = regex.replace(r"*", r"\w{0,7}")
            regex_usr = re.compile(r"[\{\[]([ \"\w]+)[\}\]]\(?(" + regex + r")\)?")
            regex_std = re.compile(r"([ (\"])(" + regex +r")([ ,.)?!:;\"'\n])")
            self.tags.append([attr_dict['id'], regex_usr, regex_std])
        elif 'regex' in attr_dict.keys():
            regex_usr = re.compile(r"[\{\[]([ \"\w]+)[\}\]]\(?(" + attr_dict['regex'] + r")\)?")
            regex_std = re.compile(r"([ (\"])(" + attr_dict['regex'] +r")([ ,.)?!:;\"'\n])")
            self.tags.append([attr_dict['id'], regex_usr, regex_std])
        else:
            return
