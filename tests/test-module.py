#!/usr/bin/env python3

import sys

import yaml
from avocado.core.job import Job
from avocado.core.suite import TestSuite

CONTAINER_IMAGE_MAPPING = {
    "CentOS Stream 9": "centos:stream9",
    "Fedora 36": "fedora:36",
    "Fedora 37": "fedora:37",
}

metadata_path = sys.argv[1]
with open(metadata_path, "rb") as m:
    metadata = yaml.load(m, Loader=yaml.SafeLoader)

test_suites = []
for platform in metadata["supported_platforms"]:
    name = platform.replace(" ", "_")
    image = CONTAINER_IMAGE_MAPPING.get(platform)
    config = {"run.spawner": "podman", "spawner.podman.image": image}

    config["resolver.references"] = metadata["tests"]
    test_suites.append(TestSuite.from_config(config, name))


with Job(test_suites=test_suites) as j:
    sys.exit(j.run())
