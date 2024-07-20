import json
from flask import request, g, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from config import auth0_config

#----------------------------------------------------------------------------#
# Auth0 Config
#----------------------------------------------------------------------------#

AUTH0_DOMAIN = auth0_config['AUTH0_DOMAIN']
ALGORITHMS = auth0_config['ALGORITHMS']
API_AUDIENCE = auth0_config['API_AUDIENCE']

#----------------------------------------------------------------------------#
# AuthError Exception
#----------------------------------------------------------------------------#
class AuthError(Exception):
    '''A standardized way to communicate auth failure modes'''
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code
    
#----------------------------------------------------------------------------#
# Auth Wrapper Methods
#----------------------------------------------------------------------------#

def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header

    *Input: None
    *Output:
       <string> token (part of the header)
    
    Conditions for Output:
       - Authorization header is available
       - header must not be malformed (i.e. Bearer XXXXX)

    """
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    elif len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    elif len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    return parts[1]

def check_permissions(permission, payload):
    ''' Check if permission is part of payload
    *Input
        <string> permission (i.e. 'post:example')
        <string> payload (decoded jwt payload)
    *Output:
         <bool> True if all conditions have been met
    
    Conditions for Output:
      - scope is included in the payload
      - requested permission string is in the payload scope array

    '''
    if 'scope' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Scope not included in JWT.'
        }, 400)

    token_scopes = payload['scope'].split()
    if permission not in token_scopes:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)
    return True

def verify_decode_jwt(token):
    ''' Decodes JWT Token or raises appropiate Error Messages

    *Input
        <string> token (a json web token)
    
    *Output 
        <string> decoded payload

    Conditions for output to be returned:
        - Auth0 token with key id (key id = kid)
        - verify the token using Auth0 /.well-known/jwks.json
        - decode the payload from the token with Auth Config on top of auth.py
        - claims need to fit

    '''
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)

        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)

    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

def requires_auth(permission=''):
    ''' Authentification Wrapper to decorate Endpoints with
    
    *Input:
        <string> permission (i.e. 'post:drink')

    uses the get_token_auth_header method to get the token
    uses the verify_decode_jwt method to decode the jwt
    uses the check_permissions method validate claims and check the requested permission

    return the decorator which passes the decoded payload to the decorated method
    '''
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except AuthError as e:
                raise e
            except Exception:
                raise AuthError({
                    'code': 'unauthorized',
                    'description': 'Permissions not found'
                }, 401)
            check_permissions(permission, payload)
            g.current_user = payload
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator
