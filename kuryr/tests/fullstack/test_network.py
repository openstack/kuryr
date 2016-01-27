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


from kuryr.tests.fullstack import kuryr_base


class NetworkTest(kuryr_base.KuryrBaseTest):
    """Test Networks operation

    Test networks creation/deletion from docker to Neutron
    """
    def test_create_delete_network_with_kuryr_driver(self):
        """Create and Delete docker network with Kuryr

           This method creates a docker network with Kuryr driver
           and tests it was created in Neutron.
           It then deletes the docker network and tests that it was
           deleted from Neutron.
        """
        res = self.docker_client.create_network(name='fakenet', driver='kuryr')
        network_id = res['Id']
        network = self.neutron_client.list_networks(name=network_id)
        self.assertEqual(1, len(network['networks']))
        self.docker_client.remove_network(network_id)
        network = self.neutron_client.list_networks(name=network_id)
        self.assertEqual(0, len(network['networks']))

    def test_create_delete_network_without_kuryr_driver(self):
        """Create and Delete docker network without Kuryr

           This method create a docker network with the default
           docker driver, It tests that it was created correctly, but
           not added to Neutron
        """
        res = self.docker_client.create_network(name='fakenet')
        network_id = res['Id']
        network = self.neutron_client.list_networks(name=network_id)
        self.assertEqual(0, len(network['networks']))
        docker_networks = self.docker_client.networks()
        network_found = False
        for docker_net in docker_networks:
            if docker_net['Id'] == network_id:
                network_found = True
        self.assertTrue(network_found)
        self.docker_client.remove_network(network_id)

    def test_create_network_with_same_name(self):
        """Create docker network with same name

           Create two docker networks with same name,
           delete them and see that neutron networks are
           deleted as well
        """
        res = self.docker_client.create_network(name='fakenet', driver='kuryr')
        network_id1 = res['Id']
        res = self.docker_client.create_network(name='fakenet', driver='kuryr')
        network_id2 = res['Id']
        network = self.neutron_client.list_networks(name=network_id1)
        self.assertEqual(1, len(network['networks']))
        network = self.neutron_client.list_networks(name=network_id2)
        self.assertEqual(1, len(network['networks']))
        self.docker_client.remove_network(network_id1)
        self.docker_client.remove_network(network_id2)
        network = self.neutron_client.list_networks(name=network_id1)
        self.assertEqual(0, len(network['networks']))
        network = self.neutron_client.list_networks(name=network_id2)
        self.assertEqual(0, len(network['networks']))
