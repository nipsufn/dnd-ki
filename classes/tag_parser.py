# tag_parser.py
"""Module detecting keywords to be used as tags
"""
from html.parser import HTMLParser
import logging

class TagParser(HTMLParser):
    __logger = None
    def __init__(self, logger):
        self.tags = []
        # extract descriptions
        self.descriptions = []
        # overwrite super.feed to pull blocks of text then call super.feed
        self.__logger = logger
        
        super().__init__()

    def handle_starttag(self, tag, attrs):
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

            self.tags.append([attr_dict['id'], regex])
        elif 'regex' in attr_dict.keys():
            self.tags.append([attr_dict['id'], attr_dict['regex']])
        else:
            return
    #def handle_data(self, data):
        #self.__logger.trace("data %s", data)
    def error(self, message):
        return
