# tag_creator.py
"""Module rewriting detected tag strings with actual tags
"""
import re
from html.parser import HTMLParser

class TagCreator(HTMLParser):
    def __init__(self, tags):
        self.current_html_tag = []
        self.tags = tags
        self.text = ""
        super().__init__()

    def handle_starttag(self, tag, attrs):
        self.current_html_tag.append(tag)
        self.text += self.get_starttag_text()

    def handle_endtag(self, tag):
        if len(self.current_html_tag) == 0 or self.current_html_tag[0] == tag:
            self.current_html_tag.pop()
        if tag == "br":
            return
        self.text += "</" + tag + ">"

    def handle_data(self, data):
        if len(self.current_html_tag) == 0:
            for pair in self.tags:
                #all user-tags `{whatever}Actual Name` or `[whatever](Actual Name)`
                regex_user = re.compile(r"[\{\[]([ \"\w]+?)[\}\]]\(?(" + pair[1] + r")\)?")
                substitute_user = r"[\1](#" + pair[0] + r")"
                data = regex_user.sub(substitute_user, data)

                #all standard tags unless it is already tagged [] or in between ><
                regex_std = re.compile(r"([ (\"])(" + pair[1] +r")([ ,.)?!:;\"'\n])")
                substitute_std = r"\1[\2](#" + pair[0] + r")\3"
                data = regex_std.sub(substitute_std, data)
        self.text += data

    def clean(self):
        self.text = ""

    def error(self, message):
        return
