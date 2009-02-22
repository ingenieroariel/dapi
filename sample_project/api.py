
import dapi
from dapi.auth.doauth import AuthOAuth

class OAuthApi(dapi.Api):
    auth = AuthOAuth()

oauth_api = OAuthApi(extends=dapi.default_api)
