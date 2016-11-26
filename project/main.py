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
        self.render("home.html")

    def post(self):
        key = self.get_argument("key", None)
        if key:
            entry = Entry.get(key)
            entry.title = self.get_argument("title")
            entry.body_source = self.get_argument("body_source")
            entry.html = tornado.escape.linkify(
                self.get_argument("body_source"))
        else:
            title = self.get_argument("title")
            slug = unicodedata.normalize("NFKD", title).encode(
                "ascii", "ignore")
            slug = re.sub(r"[^\w]+", " ", slug)
            slug = "-".join(slug.lower().strip().split())
            if not slug: slug = "entry"
            while True:
                existing = db.Query(Entry).filter("slug =", slug).get()
                if not existing or str(existing.key()) == key:
                    break
                slug += "-2"
            entry = Entry(
                author=self.current_user,
                title=title,
                slug=slug,
                body_source=self.get_argument("body_source"),
                html=tornado.escape.linkify(self.get_argument("body_source")),
            )
        entry.put()
        self.redirect("/entry/" + entry.slug)


class AdminHandler(BaseHandler):
    @administrator
    def get(self):
        self.render("admin.html", words=[])



# class ComposeHandler(BaseHandler):
#     @administrator
#     def get(self):
#         key = self.get_argument("key", None)
#         entry = Entry.get(key) if key else None
#         self.render("compose.html", entry=entry)
# 
#     @administrator
#     def post(self):
#         key = self.get_argument("key", None)
#         if key:
#             entry = Entry.get(key)
#             entry.title = self.get_argument("title")
#             entry.body_source = self.get_argument("body_source")
#             entry.html = tornado.escape.linkify(
#                 self.get_argument("body_source"))
#         else:
#             title = self.get_argument("title")
#             slug = unicodedata.normalize("NFKD", title).encode(
#                 "ascii", "ignore")
#             slug = re.sub(r"[^\w]+", " ", slug)
#             slug = "-".join(slug.lower().strip().split())
#             if not slug: slug = "entry"
#             while True:
#                 existing = db.Query(Entry).filter("slug =", slug).get()
#                 if not existing or str(existing.key()) == key:
#                     break
#                 slug += "-2"
#             entry = Entry(
#                 author=self.current_user,
#                 title=title,
#                 slug=slug,
#                 body_source=self.get_argument("body_source"),
#                 html=tornado.escape.linkify(self.get_argument("body_source")),
#             )
#         entry.put()
#         self.redirect("/entry/" + entry.slug)


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
