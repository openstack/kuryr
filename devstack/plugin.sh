#!/bin/bash
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace

ETCD_VERSION=v2.2.2

function install_etcd_data_store {

    if [ ! -f "$DEST/etcd/etcd-$ETCD_VERSION-linux-amd64/etcd" ]; then
        echo "Installing etcd server"
        mkdir $DEST/etcd
        wget https://github.com/coreos/etcd/releases/download/$ETCD_VERSION/etcd-$ETCD_VERSION-linux-amd64.tar.gz -O $DEST/etcd/etcd-$ETCD_VERSION-linux-amd64.tar.gz
        tar xzvf $DEST/etcd/etcd-$ETCD_VERSION-linux-amd64.tar.gz -C $DEST/etcd
    fi

    # Clean previous DB data
    rm -rf $DEST/etcd/db.etcd
}


function check_docker {
    if is_ubuntu; then
       dpkg -s docker-engine > /dev/null 2>&1
    else
       rpm -q docker-engine > /dev/null 2>&1
    fi
}


# main loop
if is_service_enabled kuryr; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        install_etcd_data_store
        setup_develop $KURYR_HOME

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then

        if [[ ! -d "${KURYR_ACTIVATOR_DIR}" ]]; then
            echo -n "${KURYR_ACTIVATOR_DIR} directory is missing. Creating it... "
            sudo mkdir -p ${KURYR_ACTIVATOR_DIR}
            echo "Done"
        fi

        if [[ ! -f "${KURYR_ACTIVATOR}" ]]; then
             echo -n "${KURYR_ACTIVATOR} is missing. Copying the default one... "
             sudo cp ${KURYR_DEFAULT_ACTIVATOR} ${KURYR_ACTIVATOR}
             echo "Done"
        fi

        if [[ ! -d "${KURYR_CONFIG_DIR}" ]]; then
            echo -n "${KURYR_CONFIG_DIR} directory is missing. Creating it... "
            sudo mkdir -p ${KURYR_CONFIG_DIR}
            echo "Done"
        fi

        if [[ ! -f "${KURYR_CONFIG}" ]]; then
            if [[ -f "${KURYR_DEFAULT_CONFIG}" ]]; then
                echo -n "${KURYR_CONFIG} is missing. Copying the default one... "
                sudo cp ${KURYR_DEFAULT_CONFIG} ${KURYR_CONFIG}
                echo "Done"
            else
                echo -n "${KURYR_CONFIG} and the  default config missing. Auto generating and copying one... "
                cd ${KURYR_HOME}
                oslo-config-generator --config-file=${KURYR_CONFIG_GENERATOR}
                sudo cp ${KURYR_DEFAULT_CONFIG}.sample ${KURYR_DEFAULT_CONFIG}
                sudo cp ${KURYR_DEFAULT_CONFIG} ${KURYR_CONFIG}
                cd -
            fi
        fi

        # Run etcd first
        run_process etcd-server "$DEST/etcd/etcd-$ETCD_VERSION-linux-amd64/etcd --data-dir $DEST/etcd/db.etcd --advertise-client-urls http://0.0.0.0:$KURYR_ETCD_PORT  --listen-client-urls http://0.0.0.0:$KURYR_ETCD_PORT"

        # FIXME(mestery): By default, Ubuntu ships with /bin/sh pointing to
        # the dash shell.
        # ..
        # ..
        # The dots above represent a pause as you pick yourself up off the
        # floor. This means the latest version of "install_docker.sh" to load
        # docker fails because dash can't interpret some of it's bash-specific
        # things. It's a bug in install_docker.sh that it relies on those and
        # uses a shebang of /bin/sh, but that doesn't help us if we want to run
        # docker and specifically Kuryr. So, this works around that.
        sudo update-alternatives --install /bin/sh sh /bin/bash 100

        # Install docker only if it's not already installed. The following checks
        # whether the docker-engine package is already installed, as this is the
        # most common way for installing docker from binaries. In case it's been
        # manually installed, the install_docker.sh script will prompt a warning
        # if another docker executable is found
        check_docker || {
            wget http://get.docker.com -O install_docker.sh
            sudo chmod 777 install_docker.sh
            sudo sh install_docker.sh
            sudo rm install_docker.sh
        }

        # After an ./unstack it will be stopped. So it is ok if it returns exit-code == 1
        sudo service docker stop || true

        run_process docker-engine "sudo /usr/bin/docker daemon -H tcp://0.0.0.0:$KURYR_DOCKER_ENGINE_PORT --cluster-store etcd://localhost:$KURYR_ETCD_PORT"

        run_process kuryr "sudo PYTHONPATH=$PYTHONPATH:$DEST/kuryr SERVICE_USER=admin SERVICE_PASSWORD=$SERVICE_PASSWORD SERVICE_TENANT_NAME=admin SERVICE_TOKEN=$SERVICE_TOKEN IDENTITY_URL=http://127.0.0.1:5000/v2.0 python $DEST/kuryr/scripts/run_server.py  --config-file /etc/kuryr/kuryr.conf"

    fi

    if [[ "$1" == "stack" && "$2" == "extra" ]]; then

        neutron subnetpool-create --default-prefixlen $KURYR_POOL_PREFIX_LEN --pool-prefix $KURYR_POOL_PREFIX kuryr

    fi

    if [[ "$1" == "unstack" ]]; then
        stop_process kuryr
        stop_process etcd-server
        stop_process docker-engine
    fi
fi

# Restore xtrace
$XTRACE

