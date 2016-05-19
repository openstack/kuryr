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

import sys

from oslo_log import log

from kuryr import app
from kuryr.common import config
from kuryr import controllers


config.init(sys.argv[1:])
controllers.neutron_client()
controllers.check_for_neutron_ext_support()
controllers.check_for_neutron_ext_tag()
app.debug = config.CONF.debug

log.setup(config.CONF, 'Kuryr')


def start():
    port = int(config.CONF.kuryr_uri.split(':')[-1])
    app.run("0.0.0.0", port)


if __name__ == '__main__':
    start()
