#!/usr/bin/env python3

import argparse
import json
import sys
from typing import Sequence, MutableSequence

from dresources import DAction, action
from gcp import GcpResource
from gcp_services import GcpServices


class GcpProject(GcpResource):

    def __init__(self, data: dict, gcp_services: GcpServices = GcpServices()) -> None:
        super().__init__(data=data, gcp_services=gcp_services)
        self.config_schema.update({
            "type": "object",
            "required": ["project_id"],
            "additionalProperties": False,
            "properties": {
                "project_id": {"type": "string", "pattern": "^[a-zA-Z][a-zA-Z0-9_\\-]*$"},
                "organization_id": {"type": "integer"},
                "billing_account_id": {"type": "string"},
                "apis": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "enabled": {
                            "type": "array",
                            "items": {"type": "string", "uniqueItems": True}
                        },
                        "disabled": {
                            "type": "array",
                            "items": {"type": "string", "uniqueItems": True}
                        }
                    }
                }
            }
        })

    def discover_state(self):
        project: dict = self.gcp.find_project(self.info.config['project_id'])
        if project is None:
            return None

        actual_billing: dict = self.gcp.find_project_billing_info(self.info.config['project_id'])
        if actual_billing is not None and 'billingAccountName' in actual_billing:
            project['billing_account_id']: str = actual_billing['billingAccountName'][len('billingAccounts/'):]
        else:
            project['billing_account_id']: str = None

        project['apis']: dict = {'enabled': self.gcp.find_project_enabled_apis(self.info.config['project_id'])}
        return project

    def get_actions_for_missing_state(self) -> Sequence[DAction]:
        config = self.info.config

        actions: MutableSequence[DAction] = [
            DAction(name=f"create-project",
                    description=f"Create GCP project '{self.info.config['project_id']}'")
        ]

        if 'billing_account_id' in config:
            desired_billing_account = config['billing_account_id']
            actions.append(
                DAction(name='set-billing-account',
                        description=f"Set billing account to '{desired_billing_account}'"))

        if 'apis' in config:
            # TODO: fail if the same API is both enabled & disabled

            apis = config['apis']
            if 'disabled' in apis:
                for api_name in apis['disabled']:
                    if 'enabled' in apis and api_name in apis['enabled']:
                        raise Exception(f"illegal config: the API '{api_name}' cannot be both enabled & disabled!")
                    actions.append(
                        DAction(name=f"disable-api-{api_name}",
                                description=f"Disable API '{api_name}'",
                                args=['disable_api', api_name]))
            if 'enabled' in apis:
                for api_name in apis['enabled']:
                    if 'disabled' in apis and api_name in apis['disabled']:
                        raise Exception(f"illegal config: the API '{api_name}' cannot be both enabled & disabled!")
                    actions.append(
                        DAction(name=f"enable-api-{api_name}",
                                description=f"Enable API '{api_name}'",
                                args=['enable_api', api_name]))
        return actions

    def get_actions_for_discovered_state(self, state: dict) -> Sequence[DAction]:
        actions: MutableSequence[DAction] = []
        config = self.info.config

        # update project organization if requested to (and if necessary)
        if 'organization_id' in config:
            actual_parent: dict = state['parent'] if 'parent' in state else {}
            actual_parent_id: int = int(actual_parent['id']) if 'id' in actual_parent else None
            desired_parent_id: int = config['organization_id']
            if desired_parent_id != actual_parent_id:
                actions.append(DAction(name='set-parent', description=f"Set organization to '{desired_parent_id}'"))

        # update project billing account if requested to (and if necessary)
        if 'billing_account_id' in config and config['billing_account_id'] != state['billing_account_id']:
            actions.append(
                DAction(name='set-billing-account',
                        description=f"Set billing account to '{config['billing_account_id']}'"))

        # enable/disable project APIs if requested to (and if necessary)
        if 'apis' in config:
            apis = config['apis']

            # fetch currently enabled project APIs
            actual_enabled_api_names: Sequence[str] = sorted(state['apis'])

            if 'disabled' in apis:
                # disable APIs that are currently enabled, but user requested them to be disabled
                for api_name in [api_name for api_name in apis['disabled'] if api_name in actual_enabled_api_names]:
                    actions.append(
                        DAction(name=f"disable-api-{api_name}",
                                description=f"Disable API '{api_name}'",
                                args=['disable_api', api_name]))

            if 'enabled' in apis:
                # enable APIs that are currently not enabled, but user requested them to be enabled
                for api_name in [api_name for api_name in apis['enabled'] if api_name not in actual_enabled_api_names]:
                    actions.append(
                        DAction(name=f"enable-api-{api_name}",
                                description=f"Enable API '{api_name}'",
                                args=['enable_api', api_name]))

        return actions

    def configure_action_argument_parser(self, action: str, argparser: argparse.ArgumentParser):
        super().configure_action_argument_parser(action, argparser)
        if action == 'disable_api':
            argparser.add_argument('api', metavar='NAME', help="API to disable (eg. 'cloudbuild.googleapis.com)")
        elif action == 'enable_api':
            argparser.add_argument('api', metavar='NAME', help="API to enable (eg. 'cloudbuild.googleapis.com)")

    @action
    def create_project(self, args):
        if args: pass
        config = self.info.config
        self.gcp.create_project(body={
            "projectId": self.info.config['project_id'],
            "name": self.info.config['project_id'],
            "parent": {
                'type': 'organization',
                'id': str(config['organization_id'])
            } if 'organization_id' in config and config['organization_id'] is not None else None
        })

    @action
    def set_parent(self, args):
        if args: pass
        self.gcp.update_project(project_id=self.info.config['project_id'], body={
            'parent': {
                'type': 'organization',
                'id': str(self.info.config['organization_id'])
            } if self.info.config['organization_id'] is not None else None
        })

    @action
    def set_billing_account(self, args):
        if args: pass
        desired_billing_accunt_id = self.info.config['billing_accunt_id']
        self.gcp.update_project_billing_info(project_id=self.info.config['project_id'], body={
            'billingAccountName': f"billingAccounts/{desired_billing_accunt_id}" if desired_billing_accunt_id else ""
        })

    @action
    def disable_api(self, args):
        self.gcp.disable_project_api(project_id=self.info.config['project_id'], api=args.api)

    @action
    def enable_api(self, args):
        self.gcp.enable_project_api(project_id=self.info.config['project_id'], api=args.api)


def main():
    GcpProject(json.loads(sys.stdin.read())).execute()


if __name__ == "__main__":
    main()
