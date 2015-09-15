# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import flask
import jsonschema
from neutronclient.common import exceptions as n_exceptions
from neutronclient.neutron import client
from neutronclient.v2_0 import client as client_v2
from werkzeug import exceptions as w_exceptions


DOCKER_NETNS_BASE = '/var/run/docker/netns'


def get_neutron_client_simple(url, token):
    return client.Client('2.0', endpoint_url=url, token=token)


def get_neutron_client(url, username, tenant_name, password,
                       auth_url, timeout=30):
    params = {
        'endpoint_url': url,
        'timeout': timeout,
    }

    params['username'] = username
    params['tenant_name'] = tenant_name
    params['password'] = password
    params['auth_url'] = auth_url
    return client_v2.Client(**params)


# Return all errors as JSON. From http://flask.pocoo.org/snippets/83/
def make_json_app(import_name, **kwargs):
    """Creates a JSON-oriented Flask app.

    All error responses that you don't specifically manage yourself will have
    application/json content type, and will contain JSON that follows the
    libnetwork remote driver protocol.


    { "Err": "405: Method Not Allowed" }


    See:
      - https://github.com/docker/libnetwork/blob/3c8e06bc0580a2a1b2440fe0792fbfcd43a9feca/docs/remote.md#errors  # noqa
    """
    app = flask.Flask(import_name, **kwargs)

    @app.errorhandler(n_exceptions.NeutronClientException)
    @app.errorhandler(jsonschema.ValidationError)
    def make_json_error(ex):
        response = flask.jsonify({"Err": str(ex)})
        response.status_code = 500
        if isinstance(ex, w_exceptions.HTTPException):
            response.status_code = ex.code
        elif isinstance(ex, n_exceptions.NeutronClientException):
            response.status_code = ex.status_code
        elif isinstance(ex, jsonschema.ValidationError):
            response.status_code = 400
        content_type = 'application/vnd.docker.plugins.v1+json; charset=utf-8'
        response.headers['Content-Type'] = content_type
        return response

    for code in w_exceptions.default_exceptions.iterkeys():
        app.error_handler_spec[None][code] = make_json_error

    return app


def get_sandbox_key(container_id):
    """Returns a sandbox key constructed with the given container ID.

    :param container_id: the ID of the Docker container as string
    :returns: the constructed sandbox key as string
    """
    return os.path.join(DOCKER_NETNS_BASE, container_id[:12])
