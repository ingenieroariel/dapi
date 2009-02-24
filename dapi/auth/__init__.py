
class AuthBase(object):
    def check_request(self, request):
        raise NotImplementedError()

class AuthPassThru(AuthBase):
    """
    Pass-thru authentication (aka no authentication).
    """
    
    def check_request(self, request):
        return None
