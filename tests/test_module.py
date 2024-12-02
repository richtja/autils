#!/usr/bin/env python3

import os
import sys

import yaml
from avocado.core.job import Job
from avocado.core.suite import TestSuite
from avocado.utils import process
from avocado.utils.podman import Podman

CONTAINER_IMAGE_MAPPING = {
    "CentOS Stream 9": ("redhat_based", "centos:stream9"),
    "Fedora 36": ("redhat_based", "fedora:36"),
    "Fedora 37": ("redhat_based", "fedora:37"),
}

METADATA_PATH = sys.argv[1]
COVERAGE = False
if len(sys.argv) > 2:
    COVERAGE = sys.argv[2] == "--coverage"
with open(METADATA_PATH, "rb") as m:
    metadata = yaml.load(m, Loader=yaml.SafeLoader)

images = []
test_suites = []
for platform in metadata["supported_platforms"]:
    name = platform.replace(" ", "_")
    containerfile, image_version = CONTAINER_IMAGE_MAPPING.get(platform)
    if COVERAGE:
        _, result, _ = Podman().execute(
            "build",
            "--no-cache",
            "--from",
            image_version,
            "--env",
            "COVERAGE_RUN=1",
            "-f",
            os.path.join("tests", "containerfiles", containerfile),
            ".",
        )
    else:
        _, result, _ = Podman().execute(
            "build",
            "--no-cache",
            "--from",
            image_version,
            "-f",
            os.path.join("tests", "containerfiles", containerfile),
            ".",
        )
    image = result.splitlines()[-1].decode()
    images.append(image)
    config = {"run.spawner": "podman", "spawner.podman.image": image}

    config["resolver.references"] = metadata["tests"]
    test_suites.append(TestSuite.from_config(config, name))


with Job(test_suites=test_suites) as j:
    rc = j.run()
    if COVERAGE:
        for image in images:
            _, result, _ = Podman().execute(
                "ps", "-qa", "--noheading", f"--filter=ancestor={image}"
            )
            for container in result.splitlines():
                Podman().execute(
                    "cp", f"{container.decode()}:/tmp/autils_coverage/", "./"
                )
        process.run("coverage combine ./autils_coverage")
        process.run("coverage xml")
        print(process.run("coverage report").stdout_text)

    for image in images:
        Podman().execute("image", "rm", "-f", image)
    sys.exit(rc)
