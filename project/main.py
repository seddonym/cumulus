#!/usr/bin/env python

import functools
import os.path
import re
import tornado.escape
import tornado.web
import tornado.wsgi
import unicodedata
from collections import Counter
# import nltk
import urllib
from bs4 import BeautifulSoup
from google.appengine.api import users
from models import save_words


def administrator(method):
    """Decorate with this method to restrict to site admins."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method == "GET":
                self.redirect(self.get_login_url())
                return
            raise tornado.web.HTTPError(403)
        elif not self.current_user.administrator:
            if self.request.method == "GET":
                self.redirect("/")
                return
            raise tornado.web.HTTPError(403)
        else:
            return method(self, *args, **kwargs)
    return wrapper


class BaseHandler(tornado.web.RequestHandler):
    """Implements Google Accounts authentication methods."""
    def get_current_user(self):
        user = users.get_current_user()
        if user: user.administrator = users.is_current_user_admin()
        return user

    def get_login_url(self):
        return users.create_login_url(self.request.uri)

    def get_template_namespace(self):
        # Let the templates access the users module to generate login URLs
        ns = super(BaseHandler, self).get_template_namespace()
        ns['users'] = users
        return ns


class HomeHandler(BaseHandler):
    def get(self):
        self.render("home.html", url=None)

    def post(self):
        url = self.get_argument('url')
        html = urllib.urlopen(url).read()
        soup = BeautifulSoup(html, 'html.parser')
        
        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()    # rip it out
        
        # get text
        text = soup.get_text()
        all_words = re.findall(r'\w+', text)
        
#         tagged_words = nltk.pos_tag(all_words)
#         cleaned_words = []
#         PRESERVE_CASE_TYPES = ('NNP', 'NNPS')
#         INCLUDE_TYPES_STARTS_WITH = ('NN', 'VB')
#         for word, word_type in tagged_words:
#             if any([word_type.startswith(i) for i in INCLUDE_TYPES_STARTS_WITH]):
#                 if word_type not in PRESERVE_CASE_TYPES:
#                     word = word.lower()
#                 cleaned_words.append(word)
        # TODO - improve
        cleaned_words = [word.lower() for word in all_words]
        # Remove any words that are above the max length
        # TODO
        most_common = Counter(cleaned_words).most_common(100)
        
        # Save words
        save_words(most_common)
        
        words = []
        for text, weight in most_common:
            words.append({
                'text': text,
                'weight': weight,
            })
        self.render("home.html", url=url, words=words)


class AdminHandler(BaseHandler):
    @administrator
    def get(self):
        self.render("admin.html", words=[])


settings = {
    "site_title": u"Cumulus",
    "template_path": os.path.join(os.path.dirname(__file__), "..", "templates"),
    # "ui_modules": {"Entry": EntryModule},
    "xsrf_cookies": True,
}
application = tornado.web.Application([
    (r"/", HomeHandler),
    (r"/admin", AdminHandler),
], **settings)

application = tornado.wsgi.WSGIAdapter(application)
