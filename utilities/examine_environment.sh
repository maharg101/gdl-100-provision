#!/bin/bash -x
#### Description: Examine the environment set up via quickstart
#### Written by:  maharg101 on 22nd February 2018

openstack router list
openstack router show r1

openstack network list
openstack network show net1

openstack subnet list
openstack subnet show net1

openstack security group list
openstack security group show default

openstack security group rule list default
rule_list=$(openstack security group rule list default)
rule_ids=$(echo "$rule_list" | egrep -v '\+|ID' | cut -d '|' -f 2)
for rule_id in $rule_ids
do
  openstack security group rule show $rule_id
done

openstack server list
openstack server show blog_app_1

openstack flavor list
openstack flavor show m1.tiny

openstack image list
openstack image show 'Ubuntu 16.04 LTS'
