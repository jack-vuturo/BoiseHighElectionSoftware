from __future__ import print_function
from flask import request, redirect, url_for
import json
from requests_oauthlib import OAuth2Session
from urllib.request import urlopen

class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name, id, secret):
        self.provider_name = provider_name
        self.consumer_id = id
        self.consumer_secret = secret

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('boisevotes.callback', provider=self.provider_name,
                       _external=True, _scheme='https')

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class GoogleSignIn(OAuthSignIn):
    openid_url = "https://accounts.google.com/.well-known/openid-configuration"

    def __init__(self, id, secret):
        super(GoogleSignIn, self).__init__("google", id, secret)
        self.openid_config = json.load(urlopen(self.openid_url))
        self.session = OAuth2Session(
            client_id=self.consumer_id,
            redirect_uri=self.get_callback_url(),
            scope='https://www.googleapis.com/auth/userinfo.profile openid https://www.googleapis.com/auth/userinfo.email '
        )

    def authorize(self):
        auth_url, _ = self.session.authorization_url(
            self.openid_config["authorization_endpoint"])
        return redirect(auth_url)

    def callback(self):
        if "code" not in request.args:
            return None, None

        self.session.fetch_token(
            token_url=self.openid_config["token_endpoint"],
            code=request.args["code"],
            client_secret=self.consumer_secret,
        )

        me = self.session.get(self.openid_config["userinfo_endpoint"]).json()
        return me["family_name"], me["given_name"], me["email"], me["picture"], me["sub"]