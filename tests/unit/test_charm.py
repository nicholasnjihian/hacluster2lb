# Copyright 2022 nicknjihia
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

from ops.testing import Harness

from charm import Hacluster2LbCharm

LB_INTERFACE_DATA = {
    "json_clones": r'{"cl_ks_haproxy":"res_ks_haproxy"}',
    "json_delete_resources": r'["res_ks_eth0_vip"]',
    "json_groups": r'{"grp_ks_vips":"res_ks_121f3f8_vip"}',
    "json_init_services": r'{"res_ks_haproxy":"haproxy"}',
    "json_resource_params": (
        '{"res_ks_121f3f8_vip":"params ip=\\"10.165.186.10\\" '
        'op monitor\' timeout=\\"20s\\" interval=\\"10s\\" depth=\\'
        '"0\\"","res_ks_haproxy":"meta migration-threshold=\\"INFINITY\\" '
        'failure-timeout=\\"5s\\" op monitor interval=\\"5s\\""}'
    ),
    "json_resources": (
        r'{"res_ks_121f3f8_vip":'
        r'"ocf:heartbeat:IPaddr2","res_ks_haproxy":"lsb:haproxy"}'
    ),
}


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(Hacluster2LbCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_config_changed(self):
        self.harness.set_leader(True)

        rel_id_ha = self.harness.add_relation("hacluster", "haclusterapp")
        self.assertIsInstance(rel_id_ha, int)
        self.harness.add_relation_unit(rel_id_ha, "haclusterapp/0")
        self.assertEqual(self.harness.charm.unit.status.message, "loadbalancer relation not present")

        rel_id_lb = self.harness.add_relation("loadbalancer", "loadbalancerapp")
        self.assertIsInstance(rel_id_lb, int)
        self.harness.add_relation_unit(rel_id_lb, "loadbalancerapp/0")
        self.harness.update_relation_data(
            rel_id_ha, "haclusterapp", LB_INTERFACE_DATA
        )

        ##relation_data = self.harness.get_relation_data(
        ##    rel_id_ha, self.harness.model.app.name
        ##)["json_resources"]
        ##self.assertEqual(
        ##    relation_data,
        ##    r'{"res_ks_121f3f8_vip":"ocf:heartbeat:IPaddr2","res_ks_haproxy":"lsb:haproxy"}',
        ##)

        # TODO
        # Test request response communication in LB interface for VIP and
        # port-mapping values
