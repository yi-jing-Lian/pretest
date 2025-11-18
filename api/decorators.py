from rest_framework.response import Response
from rest_framework import status

ACCEPTED_TOKEN = 'omni_pretest_token'

def validate_access_token(func):
    """
    Decorator to check if the request contains a valid access token.
    """
    def wrapper(request, *args, **kwargs):
        token = request.data.get('access_token')
        if not token or token != ACCEPTED_TOKEN:
            return Response(
                {"detail": "Invalid or missing access token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return func(request, *args, **kwargs)
    return wrapper
