# tag_creator.py
"""Module rewriting detected tag strings with actual tags
"""
import logging
from html.parser import HTMLParser

class TagCreator(HTMLParser):
    """substitute given re expr with Markdown anchor"""
    def __init__(self, tags: list, loglevel: int = logging.WARNING):
        """override parent constructor, set up and then call parent's constructor"""
        self.current_html_tag = []
        self.tags = tags
        self.text = ""
        logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(processName)s/%(threadName)s - '
            '%(pathname)s:%(lineno)d- %(name)s - %(message)s', level=loglevel)
        self.__logger = logging.getLogger(type(self).__name__)
        super().__init__()

    def handle_starttag(self, tag, attrs):
        """override parent method - store for reassembly"""
        self.current_html_tag.append(tag)
        self.text += self.get_starttag_text()

    def handle_endtag(self, tag):
        """override parent method - store for reassembly"""
        if len(self.current_html_tag) == 0 or self.current_html_tag[0] == tag:
            self.current_html_tag.pop()
        if tag == "br":
            return
        self.text += "</" + tag + ">"

    def handle_data(self, data):
        """override parent method - substitute and store for reassembly"""
        self.__logger.debug("data %s", data)
        if len(self.current_html_tag) == 0:
            for pair in self.tags:
                substitute_user = r"[\1\3](#" + pair[0] + r")"
                data = pair[1].sub(substitute_user, data)
        self.text += data
