#!/usr/bin/env python3

import json


def main():

    initialization = {
        "requires": {
            "gcloud": "/root/.config/gcloud",
            "kube": "/root/.kube"
        },
        "state_entrypoint": "/deployster/cluster-state.py"
    }

    print(json.dumps(initialization))


if __name__ == "__main__":
    main()
