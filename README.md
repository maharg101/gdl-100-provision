# GDL 100 Provision

Infrastructure provisioning code for the GDL 100 App

## Quick Start

    python ./build.py <app> <environment> <num_servers> <server_size>

For example: build.sh hello_world dev 1 m1.small


The script will return the public IP address of the launched server,
after which, you can open a browser to http://\<IP address\> and see the blog app come up !


You can destroy the environment (including related network components):

    python ./build.py <app> <environment> <num_servers> <server_size> --destroy

For help:

    python ./build.py --help


## Prerequisites

This is built to be used with Python 3.5 and above.
Use of `virtualenv` is highly recommended.

    virtualenv -p python3 venv
    source ./venv/bin/activate
    pip3 install -r ./requirements.txt


Also, before running the script you will need to:
 - source your openstackrc file
 - create a security rule to allow access to the created instances from the machine running the script
 - upload a key pair - the script will use the first ssh key pair found in your openstack account
 - enable ssh-agent if required


## Development environment and release process

 - create virtualenv as described above
 - run tests: `python -m unittest discover`
 - to modify python dependencies: add to `requirements.txt`


## General notes

This project was created as a vehicle to learn about OpenStack, Salt / Salt Cloud.

As a result, the Openstack SDK and Salt / Salt Cloud are used interchangeably (along with a liberal dose of Fabric) as
follows:

 - The OpenStack SDK is used to spin up the app server and salt master instances
 - Fabric is used to bootstrap the salt master, and place environment specific config / pillar files on the salt master
 - Salt Cloud is used to spin up the vrrp instances
 - Salt is used to install and configure everything
 

The structure of a 2-server 'dev' environment is shown below

                        <http service address>
                          /               \
    +-------------------------+       +-------------------------+
    |      vrrp-primary       |       |      vrrp-secondary     |
    |  (keepalived, haproxy)  |       |  (keepalived, haproxy)  |
    +-------------------------+       +-------------------------+
    
      +------------------+              +------------------+
      |  app-0-blog-dev  |              |  app-1-blog-dev  |
      |  (flask, nginx)  |              |  (flask, nginx)  |
      +------------------+              +------------------+
    
                         +-----------------+
                         |  salt-blog-dev  |
                         |  (salt master)  |
                         +-----------------+
 
 There are two vrrp instances which use keepalived to provide a highly available haproxy service, which load balance
 the available application servers using a round-robin approach.
 
 The application servers run the flask application behind gunicorn / nginx.
 
 The salt master (with salt cloud) is hosted on a dedicated server.

Limitations
 - Multiple environments cannot be created in a single OpenStack project due to clashing vrrp instance names.
