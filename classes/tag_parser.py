# tag_parser.py
"""Module detecting keywords to be used as tags
"""
import logging
import re
from html.parser import HTMLParser

class TagParser(HTMLParser):
    """find HTML anchors and create list of re expressions"""
    def __init__(self, loglevel: int = logging.WARNING):
        """override parent constructor, set up and then call parent's constructor"""
        self.tags = []
        self.descriptions = []
        logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(processName)s/%(threadName)s - '
            '%(pathname)s:%(lineno)d- %(name)s - %(message)s', level=loglevel)
        self.__logger = logging.getLogger(type(self).__name__)
        super().__init__()

    def handle_starttag(self, tag, attrs):
        """override parent method - assemble list of id, regex 1 and regex 2"""
        self.__logger.debug("tag %s", tag)
        if tag != "a":
            return
        attr_dict = dict(attrs)
        if 'href' in attr_dict.keys():
            return
        if 'id' not in attr_dict.keys():
            return
        if 'pattern' in attr_dict.keys() or 'regex' in attr_dict.keys():
            regex = ""
            if 'pattern' in attr_dict.keys():
                pattern_list = sorted(attr_dict['pattern'].split(','), key=len,
                                    reverse=True)
                regex = '|'.join(pattern_list) if pattern_list \
                    else attr_dict['pattern']
                regex = regex.replace(r"*", r"\w{0,7}")
            else:
                regex = attr_dict['regex']
            regex_std = re.compile(r"[\{\[]([ \-'\"\w]+?)[\}\]]\(?(" + regex + r")\)?"
                r"|(?<=[ (\"])(" + regex + r")(?=[ ,.)?!:;\"'\n])")
            self.tags.append([attr_dict['id'], regex_std])
        else:
            return
