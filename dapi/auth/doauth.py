
from django.utils.translation import ugettext as _

from oauth.oauth import OAuthError
from oauth_provider.decorators import CheckOAuth
from oauth_provider.utils import send_oauth_error

from dapi.auth import AuthBase

class AuthOAuth(AuthBase):
    def check_request(self, request):
        if CheckOAuth.is_valid_request(request):
            try:
                CheckOAuth.validate_token(request)
            except OAuthError, e: 
                return send_oauth_error(e)
        else:
            return send_oauth_error(OAuthError(_("Invalid request parameters.")))
        return None
