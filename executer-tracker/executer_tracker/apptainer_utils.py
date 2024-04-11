"""Utils related to Apptainer images.

Includes the ApptainerImagesManager class, which is used to fetch Apptainer
images from a remote storage and cache them locally.
"""
import os
import re
import subprocess

import fsspec
from absl import logging


class ApptainerImageNotFoundError(Exception):
    pass


class ApptainerImagesManager:
    """Downloads and caches Apptainer .sif images.

    Attributes:
        local_cache_dir: Path to the local directory where the Apptainer
            images will be cached.
        remote_storage_filesystem: fsspec filesystem object used to retrieve
            the Apptainer images from the remote storage.
        remote_storage_dir: Path to the directory in the remote storage where
            the Apptainer images are stored.
    """

    def __init__(
        self,
        local_cache_dir: str,
        remote_storage_filesystem: fsspec.spec.AbstractFileSystem,
        remote_storage_dir: str,
    ):
        self._local_cache_dir = local_cache_dir
        os.makedirs(self._local_cache_dir, exist_ok=True)

        self._remote_storage_filesystem = remote_storage_filesystem
        self._remote_storage_dir = remote_storage_dir

    def _normalize_image_uri(self, image_uri: str) -> str:
        """Check if the image URI is fully qualified.

        If not, include the default URI prefix 'docker://'.
        """
        if "://" in image_uri:
            uri_prefix, image_name = image_uri.split("://")
        else:
            uri_prefix = "docker"
            image_name = image_uri

        return f"{uri_prefix}://{image_name}"

    def _image_uri_to_sif_name(self, image_uri: str) -> str:
        """Converts a image URI to a SIF image name.

        Note that the conversion must follow the same conversion used in the
        Cloud Build trigger that converts Docker images to Apptainer images.
        Cloud Build definition is in .gcloud/build_apptainer_images.yaml.

        Example:
            "docker://inductiva/kutu:openfoam-foundation_v8_dev" ->
                "docker_inductiva_kutu_openfoam-foundation_v8_dev.sif"
        """
        return re.sub(r"://|:|/", "_", image_uri) + ".sif"

    def _apptainer_pull(self, image_uri: str, sif_local_path: str):
        """Pulls the image from Docker Hub and converts it to a SIF image."""
        logging.info("Pulling image from Docker Hub...")

        try:
            subprocess.run(
                [
                    "apptainer",
                    "pull",
                    sif_local_path,
                    image_uri,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise ApptainerImageNotFoundError(
                f"Failed to pull image: {image_uri}") from e
        except FileNotFoundError as e:
            raise ApptainerImageNotFoundError("Apptainer not available.") from e

    def get(self, image: str) -> str:
        """Makes the requested Apptainer image available locally.

        If the image is not available in the local directory, it is attempted
        to be fetched from the remote storage. If it is not available in the
        remote storage, it is pulled and coverted with the apptainer pull
        command and the provided image URI.

        Args:
            image: String representing the image to be converted. If it has
                the .sif extension, it is considered a SIF image name.
                Otherwise, it is considered a Docker image URI and is converted
                to the expected SIF image name.

        Returns:
            The path to the local Apptainer image file.

        Raises:
            ApptainerImageNotFoundError: If the image is not found in the
                remote storage and cannot be pulled.
        """

        logging.info("Fetching SIF image for Docker image: %s", image)

        if image.endswith(".sif"):
            sif_image_name = image
        else:
            image_uri = self._normalize_image_uri(image)
            sif_image_name = self._image_uri_to_sif_name(image_uri)

        sif_local_path = os.path.join(self._local_cache_dir, sif_image_name)
        sif_remote_path = os.path.join(self._remote_storage_dir, sif_image_name)

        if os.path.exists(sif_local_path):
            logging.info("SIF image found locally: %s", sif_image_name)
            return sif_local_path

        logging.info("SIF image not found locally: %s", sif_image_name)

        if self._remote_storage_filesystem.exists(sif_remote_path):
            logging.info("SIF image found in remote storage: %s",
                         sif_image_name)
            logging.info("Downloading from remote remote storage...")
            self._remote_storage_filesystem.download(
                sif_remote_path,
                sif_local_path,
            )
            logging.info("Downloaded SIF image to: %s", sif_local_path)
            return sif_local_path

        logging.info("SIF image not found in remote storage: %s",
                     sif_image_name)

        self._apptainer_pull(image_uri, sif_local_path)

        return sif_local_path
