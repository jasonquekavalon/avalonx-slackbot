import os
import time
import logging

import requests
import jwt

import config as cfg

logger = logging.getLogger()


def get_token():
    if os.getenv("PROJECT_ID") == "alfred-dev-emulator":
        # Don't authenticate when testing
        return "Bearer fake-token"

    IS_SANDBOX = True
    KEY_FILE = cfg.KEY_FILE
    ISSUER = cfg.ISSUER
    SUBJECT = cfg.SUBJECT

    DOMAIN = 'test' if IS_SANDBOX else 'login'

    with open(KEY_FILE) as fd:
        private_key = fd.read()

    logger.debug('Generating signed JWT assertion...')
    claim = {
        'iss': ISSUER,
        'exp': int(time.time()) + 300,
        'aud': 'https://{}.salesforce.com'.format(DOMAIN),
        'sub': SUBJECT,
    }

    assertion = jwt.encode(claim, private_key, algorithm='RS256', headers={'alg': 'RS256'}).decode('utf8')

    logger.debug('Making OAuth request...')
    r = requests.post('https://{}.salesforce.com/services/oauth2/token'.format(DOMAIN), data={
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': assertion,
    })

    return r.json()['access_token']
