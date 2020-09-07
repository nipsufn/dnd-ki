# tag_parser.py
"""Module detecting keywords to be used as tags
"""
from html.parser import HTMLParser

class TagParser(HTMLParser):
    def __init__(self):
        self.tags = []
        super().__init__()

    def handle_starttag(self, tag, attrs):
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
    def error(self, message):
        return
