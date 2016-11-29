#!/usr/bin/env python

import functools
from decimal import Decimal, ROUND_UP
import os.path
import re
import tornado.web
import tornado.wsgi
from collections import Counter
from sqlalchemy import desc
import urllib
from bs4 import BeautifulSoup
from google.appengine.api import users
from models import save_words, session, Word


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
    """Implements Google Accounts authentication methods.
    """
    def get_current_user(self):
        user = users.get_current_user()
        if user:
            user.administrator = users.is_current_user_admin()
        return user

    def get_login_url(self):
        return users.create_login_url(self.request.uri)

    def get_template_namespace(self):
        # Let the templates access the users module to generate login URLs
        namespace = super(BaseHandler, self).get_template_namespace()
        namespace['users'] = users
        return namespace


class HomeHandler(BaseHandler):
    """The home page.  This contains a form that allows the
    submission of a URL, that will then be generated as a tag cloud
    containing the 100 most frequent words on that page.
    """
    def get(self):
        self.render("home.html", url=None)

    def post(self):
        url = self.get_argument('url')
        try:
            html = urllib.urlopen(url).read()
        except:
            self.render("home.html", url=url, error=True)
            return
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get the words
        text = soup.get_text()
        all_words = re.findall(r'\w+', text)

        # import nltk
        # tagged_words = nltk.pos_tag(all_words)
        # cleaned_words = []
        # PRESERVE_CASE_TYPES = ('NNP', 'NNPS')
        # INCLUDE_STARTS_WITH = ('NN', 'VB')
        # for word, word_type in tagged_words:
        #     if any([word_type.startswith(i) for i in INCLUDE_STARTS_WITH]):
        #         if word_type not in PRESERVE_CASE_TYPES:
        #             word = word.lower()
        #         cleaned_words.append(word)
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
        self.render("home.html", url=url, words=words, error=False)


class ArchiveHandler(BaseHandler):
    """Handler for the archive page.  Accessible only by administrators,
    it lists all the words that have been ever generated in our tag clouds,
    together with the total frequency.
    """
    RESULTS_PER_PAGE = 30

    @administrator
    def get(self):
        page = int(self.get_argument('page', default=1))
        all_words = session.query(Word).order_by(desc('frequency'))
        word_count = all_words.count()
        number_of_pages = int((Decimal(word_count) / self.RESULTS_PER_PAGE)
                              .quantize(1, ROUND_UP))
        print('Page %s' % page)
        print('Number of pages %s' % number_of_pages)
        if page > number_of_pages:
            raise tornado.web.HTTPError(404)
        offset = self.RESULTS_PER_PAGE * (page - 1)
        words = all_words.limit(self.RESULTS_PER_PAGE).offset(offset)
        self.render("archive.html",
                    words=words, page=page, word_count=word_count,
                    number_of_pages=number_of_pages)


settings = {
    "site_title": u"Cumulus",
    "template_path": os.path.join(os.path.dirname(__file__), "..",
                                  "templates"),
    "xsrf_cookies": True,
}

application = tornado.web.Application([
    (r"/", HomeHandler),
    (r"/archive", ArchiveHandler),
], **settings)


application = tornado.wsgi.WSGIAdapter(application)
