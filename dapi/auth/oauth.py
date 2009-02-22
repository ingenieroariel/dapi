
from dapi.auth import AuthBase

class AuthOAuth(AuthBase):
    def check_request(self, request):
        print "checking request"
