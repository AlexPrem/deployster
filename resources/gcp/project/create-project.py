#!/usr/bin/env python3

import json
import sys

from googleapiclient.discovery import build

from deployster.gcp.services import wait_for_resource_manager_operation


def main():
    params = json.loads(sys.stdin.read())
    name = params['name']
    properties = params['properties']

    request_body = {
        "projectId": name,
        "name": name
    }

    if 'organization_id' in properties:
        request_body['parent'] = {
            'type': 'organization',
            'id': str(properties['organization_id'])
        }

    result = build(serviceName='cloudresourcemanager', version='v1').projects().create(body=request_body).execute()
    project = wait_for_resource_manager_operation(result)
    print(json.dumps({'project': project}))


if __name__ == "__main__":
    main()
