#!/usr/bin/env python

import functools
import os.path
import re
import tornado.escape
import tornado.web
import tornado.wsgi
import unicodedata

from google.appengine.api import users


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
        results = {'speak': 3, 'sandwich': 9, 'jam': 1}
        words = []
        for text, weight in results.items():
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
