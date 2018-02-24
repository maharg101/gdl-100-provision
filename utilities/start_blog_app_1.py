from __future__ import print_function

import os

from openstack import connection

conn = connection.Connection(
    region_name=os.environ['OS_REGION_NAME'],
    auth=dict(
        auth_url=os.environ['OS_AUTH_URL'],
        username=os.environ['OS_USERNAME'],
        password=os.environ['OS_PASSWORD'],
        project_id=os.environ['OS_PROJECT_ID'],
        user_domain_id=os.environ['OS_USER_DOMAIN_NAME'],
    ),
    compute_api_version='2',
    identity_interface='internal',
)


# openstack server show blog_app_1
server = conn.compute.get_server(conn.compute.find_server('blog_app_1'))

if server.status == 'ACTIVE':
    print('server is already active')
else:
    conn.compute.start_server(server)

