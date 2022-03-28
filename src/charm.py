#!/usr/bin/env python3
# Copyright 2022 nicknjihia
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus,BlockedStatus

logger = logging.getLogger(__name__)


class Hacluster2LbCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        #self.framework.observe(self.on.config_changed, self._on_config_changed)
        #self.framework.observe(self.on.upgrade_charm, self._on_config_changed)
        #self.framework.observe(self.on.hacluster_relation_joined, self._on_config_changed)
        #self.framework.observe(self.on.hacluster_relation_changed, self._on_config_changed)
        #self.framework.observe(self.on.hacluster_relation_broken, self._on_config_changed)
        #self.framework.observe(self.on.loadbalancer_relation_joined, self._on_config_changed)
        #self.framework.observe(self.on.loadbalancer_relation_changed, self._on_config_changed)
        #self.framework.observe(self.on.loadbalancer_relation_broken, self._on_config_changed)
        for event in [
            self.on.config_changed,
            self.on.upgrade_charm,
            self.on["hacluster"].relation_joined,
            self.on["hacluster"].relation_changed,
            self.on["hacluster"].relation_broken,
            self.on["loadbalancer"].relation_joined,
            self.on["loadbalancer"].relation_changed,
            self.on["loadbalancer"].relation_broken
        ]:
            self.framework.observe(event, self._on_config_changed)
        self._stored.set_default(things=[])

    def _on_config_changed(self, event: ops.charm.Event):
        """Manages the change of configuration or the relation(s).

        The method checks if the hacluster or loadbalancer relation is present and if absent,
        the charm is blocked. The method will then recover the hacluster
        interface resource information and extract the VIP which will be
        to the loadbalancer along with the port mapping.
        """
        if not self.model.relations["hacluster"]:
           self.unit.status = BlockedStatus("hacluster relation not present")
        if not self.model.relations["loadbalancer"]:
           self.unit.status = BlockedStatus("loadbalancer relation not present")
        ha_provider_relation = self.model.get_relation("hacluster")
        lb_provider_relation = self.model.get_relation("loadbalancer")
        vip_info = [key for key, val in ha_provider_relation.data["json_resource_params"].items() if v=="ocf:heartbeat:IPaddr2"]
        if len(vip_info) == 0:
            self.unit.status = BlockedStatus("No VIP provided by hacluster
relation")
            return
        elif len(vip_info) > 1:
            self.unit.status = BlockedStatus("More than one VIP provided by
the hacluster relation")
            return
        else:
            vip = ha_provider_relation.data["json_resources"](vip_info[0])
            if not (self.unit.is_leader() and self.lb_provider.is_available):
                return
            request = self.lb_provider.get_request("lb-consumer")
            
#        current = self.config["thing"]
#        if current not in self._stored.things:
#            logger.debug("found a new thing: %r", current)
#            self._stored.things.append(current)

if __name__ == "__main__":
    main(Hacluster2LbCharm)
