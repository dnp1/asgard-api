# encoding: utf-8

import sys
import json

import requests

from hollowman import conf


def replay_request(request, destination_url):
    to_url = "{}{}".format(destination_url, request.path)
    params = [(key, value)
              for key, value in request.args.items(multi=True)]
    headers = dict(request.headers)
    headers.pop("Content-Length", None)
    headers['Authorization'] = conf.MARATHON_AUTH_HEADER
    method = request.method.lower()
    if method in ['put', 'post'] and request.is_json:
        request_data = json.loads(request.data)
        request_data.pop("version", None)
        request_data.pop("fetch", None)
        request.data = json.dumps(request_data)
    return getattr(requests, method)(to_url, params=params, headers=headers, data=request.data)
