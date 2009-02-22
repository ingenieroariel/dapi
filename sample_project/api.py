
import dapi

try:
    import oauth
    import oauth_provider
except ImportError:
    oauth_support = False
else:
    oauth_support = True

if oauth_support:
    from dapi.auth.doauth import AuthOAuth
    
    class OAuthApi(dapi.Api):
        auth = AuthOAuth()
        
    oauth_api = OAuthApi(extends=dapi.default_api)
