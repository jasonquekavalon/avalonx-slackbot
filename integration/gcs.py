"""Super basic Google Cloud Storage mock"""
import pathlib
import os

from log import log

logger = log.get_logger()


class GCSMock:
    """Bare-bones Google Cloud Storage mock"""

    def __init__(self, project_id):
        logger.info("Emulator: Creating GCS mock...")
        self.project_id = project_id
        self.bucket = GCSBucket(project_id)

    def get_bucket(self, project_id):
        return self.bucket


class GCSBucket:
    """Bare-bones Google Cloud Storage Bucket mock"""

    def __init__(self, bucket_name):
        self.name = bucket_name
        self.blob_name = None

    def blob(self, blob_name):
        self.blob_name = blob_name
        return self

    def download_to_filename(self, filepath):
        """Emulate downloading a file by copying the local mp file stored in test_artifacts"""
        import shutil
        logger.info("Emulator: Copying mp file to {}...".format(filepath))
        pathlib.Path(os.path.dirname(filepath)).mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.blob_name, filepath)

    def upload_from_filename(self, file_path):
        pass


def storage_client_mock(project_id):
    return GCSMock(project_id)
