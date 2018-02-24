# GDL 100 Provision

Provisioning code for the GDL 100 App

## Quick Start

    build.sh <app> <environment> <num_servers> <server_size>

For example: build.sh hello_world dev 1 t1.micro


The script will return the public IP address of the launched server,
after which, you can open a browser to http://\<IP address\> and see the blog app come up !


## Prerequisites

This is built to be used with Python 3.5 and above.
Use of `virtualenv` is highly recommended.

    virtualenv -p python3 venv
    source ./venv/bin/activate
    pip3 install -r ./requirements.txt


## Development environment and release process

 - create virtualenv as described above
 
 - run development server in debug mode: `make run`; Flask will restart if source code is modified
 
 - run tests: TODO

 - to modify python dependencies: add to `requirements.txt`



## Deployment

TODO
