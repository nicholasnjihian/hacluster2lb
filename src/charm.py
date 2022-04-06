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

from loadbalancer_interface import LBProvider
from ops.charm import CharmBase
from ops.framework import EventBase, StoredState
from ops.main import main
from ops.model import BlockedStatus

logger = logging.getLogger(__name__)


class Hacluster2LbCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        logger.debug("Initializing hacluster2lb charm")

        for event in [
            self.on.config_changed,
            self.on.upgrade_charm,
            self.on["hacluster"].relation_joined,
            self.on["hacluster"].relation_changed,
            self.on["hacluster"].relation_broken,
            self.on["loadbalancer"].relation_joined,
            self.on["loadbalancer"].relation_changed,
            self.on["loadbalancer"].relation_broken,
        ]:
            self.framework.observe(event, self._on_config_changed)
        self._stored.set_default(things=[])

    def _on_config_changed(self, event: EventBase):
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
        vip_info = [
            key
            for key, val in ha_provider_relation.data[self.model.app][
                "json_resource_params"
            ].items()
            if val == "ocf:heartbeat:IPaddr2"
        ]
        # vip_info = vip_info.split("")
        if len(vip_info) == 0:
            self.unit.status = BlockedStatus("No VIP provided" "by hacluster relation")
            return
        elif len(vip_info) > 1:
            self.unit.status = BlockedStatus(
                "More than one VIP" "provided by the hacluster relation"
            )
            return
        else:
            vip = ha_provider_relation.data[self.model.app]["json_resources"](
                vip_info[0]
            )
            # port-mapping =
            if not (self.unit.is_leader() and self.lb_provider.is_available):
                return
            try:
                self.lb_provider = LBProvider(self, "loadbalancer")
                request = self.lb_provider_relation.get_request("lb-consumer")
                request.protocol = request.protocols.tcp
                request.port_mapping = {
                    # self.config["service-port"]: {port-mapping}
                }
                request.ingress_address = vip
                request.public = False  # Keep it as internal, maybe a config in
                # the future? -> `self.config["public"]`
                self.lb_provider.send_request(request)
            except Exception as _:
                pass  # TODO


if __name__ == "__main__":
    main(Hacluster2LbCharm)
