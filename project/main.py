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


class BaseHandler(tornado.web.RequestHandler):
    """Base RequestHandler for all handlers on the site.
    Implements Google's authentication methods so we don't have to
    implement any login ourselves.
    """
    def get_current_user(self):
        """Returns the currently logged in user.
        """
        user = users.get_current_user()
        if user:
            user.administrator = users.is_current_user_admin()
        return user

    def get_login_url(self):
        """Returns the URL for a user to log in.
        """
        return users.create_login_url(self.request.uri)

    def get_template_namespace(self):
        """Let the templates access the users module to generate login URLs.
        """
        namespace = super(BaseHandler, self).get_template_namespace()
        namespace['users'] = users
        return namespace


def administrators_only(method):
    """Decorate with this method to restrict to site admins.
    Usage:
        class MyHandler(BaseHandler):
            @administrators_only
            def get(self):
                ...
    """
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

        # TODO - nltk is great for parsing words, but is difficult to deploy
        # on Google Cloud.  Here's how we might do it:
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
        
        cleaned_words = [word.lower() for word in all_words]
        
        # Remove any words that are above the max length
        cleaned_words = [word for word in cleaned_words \
                         if len(word) <= Word.MAX_WORD_LENGTH]
        
        # Remove some common words that we're not interested in
        IGNORE_WORDS = ('the', 'a', 'an', 'no' , 'with', 'at', 'from', 'into',
                        'of', 'to', 'in', 'for', 'on', 'by', 'but', 'she', 'he',
                        'her', 'his', 'it', 'and', 'or', 's', 'as', 'we', 'or',
                        'this', 'that', 'your', 'you')
        cleaned_words = [word for word in cleaned_words \
                         if word not in IGNORE_WORDS]
        
        # Get the 100 most common words
        most_common = Counter(cleaned_words).most_common(100)

        # Save the words in the database
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

    @administrators_only
    def get(self):
        # Get all the words, ordered by most frequent first.
        all_words = session.query(Word).order_by(desc('frequency'))
        
        # Paginate, raising a 404 if the page isn't valid
        page = int(self.get_argument('page', default=1))
        word_count = all_words.count()
        number_of_pages = int((Decimal(word_count) / self.RESULTS_PER_PAGE)
                              .quantize(1, ROUND_UP))
        if page < 0 or page > number_of_pages:
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
