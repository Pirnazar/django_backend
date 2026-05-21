from rest_framework.exceptions import APIException
from rest_framework import status

class ApplicationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Application error occurred.'
    default_code = 'application_error'

    def __init__(self, detail=None, code=None, status_code=None):
        if detail is not None:
            self.detail = detail
        else:
            self.detail = self.default_detail
        
        if code is not None:
            self.code = code
        else:
            self.code = self.default_code
            
        if status_code is not None:
            self.status_code = status_code
            
class TransitionNotAllowed(ApplicationError):
    default_detail = 'Status transition is not allowed.'
    default_code = 'transition_not_allowed'
