# GDL 100 Provision

Infrastructure provisioning code for the GDL 100 App

## Quick Start

    python ./build.py <app> <environment> <num_servers> <server_size>

For example: build.sh hello_world dev 1 t1.micro


The script will return the public IP address of the launched server,
after which, you can open a browser to http://\<IP address\> and see the blog app come up !

*N.B. load balancing isn't included yet. At present the script returns the public address of each server*

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


Also you will need to source your openstackrc file before running the script.


## Development environment and release process

 - create virtualenv as described above
 
 - run tests: `python -m unittest discover`

 - to modify python dependencies: add to `requirements.txt`


