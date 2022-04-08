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

import json
import logging
import re
from ipaddress import ip_address

from loadbalancer_interface import LBProvider
from ops.charm import CharmBase
from ops.framework import EventBase, StoredState
from ops.main import main
from ops.model import BlockedStatus

logger = logging.getLogger(__name__)

PATTERN = r"\d{1,3}?\.\d{1,3}?\.\d{1,3}?\.\d{1,3}?"


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
        self.lb_provider = LBProvider(self, "loadbalancer")

    def _on_config_changed(self, event: EventBase):
        """Manages the change of configuration or the relation(s).

        The method checks if the hacluster or loadbalancer relation is present and if absent,
        the charm is blocked. The method will then recover the hacluster
        interface resource information and extract the VIP which will be
        to the loadbalancer along with the port mapping.
        """

        # Check if the relations are present, return otherwise
        if not self.model.relations["hacluster"]:
            self.unit.status = BlockedStatus("hacluster relation not present")
            return
        if not self.model.relations["loadbalancer"]:
            self.unit.status = BlockedStatus("loadbalancer relation not present")
            return
        ha_provider_relation = self.model.get_relation("hacluster")
        # Check if data is present in the hacluster relation, return otherwise
        if "json_resources" not in ha_provider_relation.data[ha_provider_relation.app]:
            self.unit.status = BlockedStatus("Waiting for hacluster data")
            return
        if (
            "json_resource_params"
            not in ha_provider_relation.data[ha_provider_relation.app]
        ):
            self.unit.status = BlockedStatus("Waiting for hacluster data")
            return

        json_resources = ha_provider_relation.data[ha_provider_relation.app][
            "json_resources"
        ]
        json_resources = json.loads(json_resources)

        vip_field = [
            key for key, val in json_resources.items() if val == "ocf:heartbeat:IPaddr2"
        ][0]

        json_resource_params = ha_provider_relation.data[ha_provider_relation.app][
            "json_resource_params"
        ]
        json_resource_params = json.loads(json_resource_params)
        vip_info = json_resource_params[vip_field]

        vip_address = []
        counter = 0

        for match in re.finditer(PATTERN, vip_info):
            if counter > 1:
               self.unit.status = BlockedStatus(
                   "More than one VIP" "provided by the hacluster relation"
               )
               return
            start = match.start()
            end = match.end()
            ip_address_match  = vip_info[start:end]
            try:
                # Determine whether the match above is a valid address
                addr = ip_address(ip_address_match)
                logging.debug("VIP address retrieved: %s", repr(addr))
                vip_address.append(ip_address_match)
                # Increase counter as address match is valid ip address
                counter += 1
            except ValueError as err:
                # Only log an error when IP address match is an invalid
                # address
                logging.error("%s", repr(err))


        if len(vip_address) == 0:
            self.unit.status = BlockedStatus("No VIP provided" "by hacluster relation")
            return
        else:
            vip = vip_address[0]
            # port-mapping =
            if not (self.unit.is_leader() and self.lb_provider.is_available):
                return

            try:
                request = self.lb_provider_relation.get_request("lb-consumer")
                request.protocol = request.protocols.tcp
                request.port_mapping = {
                    80: self.config["service-port"]  # TODO Need to edit this
                }
                request.ingress_address = vip
                request.public = False  # Keep it as internal, maybe a config in
                # the future? -> `self.config["public"]`
                self.lb_provider.send_request(request)
            except Exception as err:
                logging.debug("Unable to send request to LB: %s", repr(err))  # TODO


if __name__ == "__main__":
    main(Hacluster2LbCharm)
