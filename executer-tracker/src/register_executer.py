"""Module for registering an executer with the API."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict
from uuid import UUID

import requests
from absl import logging
from utils import gcloud, host

REGISTER_EXECUTER_ENDPOINT = "/executers/register"


def _get_executer_info() -> Dict:
    cpu_info = host.get_cpu_info_verbose()
    cpu_count = host.get_cpu_count()
    memory = host.get_total_memory()

    common_info = {
        "create_time": datetime.now(timezone.utc).isoformat(),
        "cpu_count_logical": cpu_count.logical,
        "cpu_count_physical": cpu_count.physical,
        "memory": memory,
        "cpu_info": cpu_info,
    }

    logging.info("Executer resources:")
    logging.info("\t> CPUs (logical): %s", cpu_count.logical)
    logging.info("\t> CPUs (physical): %s", cpu_count.physical)
    logging.info("\t> Memory: %s B", memory)

    if gcloud.is_running_on_gcloud_vm():
        vm_info = gcloud.get_vm_info()
        if not vm_info:
            raise RuntimeError("Failed to get VM info.")

        provider_specific_info = {
            "type": "gcloud",
            "vm_type": vm_info.type,
            "vm_name": vm_info.name,
            "vm_id": vm_info.id,
            "preemptible": vm_info.preemptible,
            "vm_metadata": vm_info.metadata,
        }

        logging.info("Running on GCloud VM:")
        logging.info("\t> VM type: %s", vm_info.type)
        logging.info("\t> VM preemptible: %s", vm_info.preemptible)
    else:
        provider_specific_info = {
            "type": "inductiva-hardware",
        }
        logging.logging.info("Running on Inductiva machine.")

    return {
        **common_info,
        "host_info": provider_specific_info,
    }


@dataclass
class ExecuterInfo:
    id: int
    redis_stream: str
    redis_consumer_group: str
    redis_consumer_name: str


def register_executer(api_url: str) -> UUID:
    """Registers an executer in the API.

    This function inspects the environment of the executer and makes a request
    to the API to register it with the right information. The function returns
    a unique ID for the executer in the scope of the API, that it should use,
    for instance, when logging events.
    """

    url = f"{api_url}{REGISTER_EXECUTER_ENDPOINT}"

    executer_info = _get_executer_info()

    logging.info("Registering executer with the API...")
    r = requests.post(
        url=url,
        json=executer_info,
        timeout=5,
    )

    if r.status_code != 202:
        raise RuntimeError(f"Failed to register executer: {r.text}")

    executer_id = r.json()["uuid"]

    logging.info("Executer registered successfully:")
    logging.info("\t> Executer ID: %s", executer_id)

    return executer_id
