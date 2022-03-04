# hacluster2lb
Convert hacluster to lb endpoint

## Description
This is a subordinate charm that converts an hacluster relation endpoint to a LB endpoint.
It allows to run clustered services across different subnets or in a fan-network.

## Usage

To deploy this charm, run juju for example:
```
juju deploy keystone
juju deploy containers-azure-integrator
juju deploy hacluster2lb
juju config keystone vip=<VIP>
juju add-relation keystone:juju-info hacluster2lb
juju add-relation keystone:hacluster hacluster2lb
juju add-relation containers-azure-integrator:lb-consumers hacluster2lb
```

### Port Mapping
The hacluster2lb charm needs to have a value for the Virtual IP (VIP) as well as
the loadbalancer endpoint. The loadbalancer needs to have a port that maps the
service port to the loadbalancer port.

To add the port mapping the charm needs to be configured as follows:
```
juju config hacluster2lb port-mapping=\
"{
  'LB-PORT': 'SERVICE-PORT',
  ...
}"
```

## Relations

### Provides Hacluster

hacluster2lb provides the hacluster endpoint and learns the parameters from that relation.

### Requires Loadbalancer

hacluster2lb converts the hacluster parameters into loadbalancer information
