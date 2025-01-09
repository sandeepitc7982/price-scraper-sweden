import os
from loguru import logger
from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient

from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)


if "DATABRICKS_RUNTIME_VERSION" in os.environ:
    logger.info("Found databricks environment")
    pass
else:
    # Mock dbutils or leave it empty for non-Databricks environments
    class MockDBUtils:
        def secrets(self):
            pass

    dbutils = MockDBUtils()


class AzureDataLakeStorage:
    def __init__(self, config):
        try:
            self.config = config
            self.initialize_secrets(config)
            self.authenticate_with_service_principal(
                self.tenant_id, self.client_id, self.key
            )
            self.initialize_datalake_client(self.account_name)
        except Exception as e:
            logger.error(f"Unable to initialize ADLS. Due to {e}")

    def initialize_secrets(self, config):
        # Tenant ID for your Azure Subscription
        self.tenant_id = dbutils.secrets.get(
            scope=config["adls"]["scope_type"], key=config["adls"]["tenant_id"]
        )
        # Your Service Principal App ID
        self.client_id = dbutils.secrets.get(
            scope=config["adls"]["scope_type"],
            key=config["adls"]["service_client_id"],
        )
        # Your Service Principal Password
        self.key = dbutils.secrets.get(
            scope=config["adls"]["scope_type"], key=config["adls"]["service_secret"]
        )
        # Your ADLS account name
        self.account_name = dbutils.secrets.get(
            scope=config["adls"]["scope_type"],
            key=config["adls"]["storage_account_name"],
        )
        # Container Name
        self.container_name = dbutils.secrets.get(
            scope=config["adls"]["scope_type"], key=config["adls"]["container_name"]
        )
        # Initial Path in container for folder.
        self.initial_path = dbutils.secrets.get(
            scope=config["adls"]["scope_type"], key=config["adls"]["initial_path"]
        )

    def authenticate_with_service_principal(self, tenant_id, client_id, key):
        logger.info("Authenticating Service Principal Client Access...")
        self.credentials = ClientSecretCredential(tenant_id, client_id, key)
        logger.info("Authentication Successful !")

    def initialize_datalake_client(self, account_name):
        logger.info("Initializing datalake client object")
        account_url = f"https://{account_name}.dfs.core.windows.net"
        self.service_client = DataLakeServiceClient(
            account_url=account_url, credential=self.credentials
        )
        logger.info("Initialized datalake client object")

    # By default, we need to load yesterday data in case of any model is fail to scrape
    def download_folder_from_adls(
        self, adls_folder_path=yesterday_dashed_str_with_key(), local_folder_path=None
    ):
        try:
            if local_folder_path is None:
                local_folder_path = (
                    self.config["output"]["directory"] + yesterday_dashed_str_with_key()
                )
            adls_folder_path = self.initial_path + "/" + adls_folder_path
            logger.info(
                f"Starting to download files from {adls_folder_path} to {local_folder_path}"
            )
            file_system_client = self.service_client.get_file_system_client(
                self.container_name
            )
            paths = file_system_client.get_paths(path=adls_folder_path)

            [
                self.process_path_to_download(
                    path, local_folder_path, file_system_client
                )
                for path in paths
            ]

            logger.info("All Files Downloaded !")
        except Exception as e:
            logger.error(f"Unable to download files from ADLS. Due to {e}")

    def process_path_to_download(self, path, local_folder_path, file_system_client):
        if not path.is_directory:
            logger.info(f"Downloading: {path.name} to {local_folder_path}")
            file_name = path.name.replace(local_folder_path, "").lstrip("/")
            local_file_path = os.path.join(local_folder_path, file_name)

            # Create directories if they don't exist
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # Download file
            file_client = file_system_client.get_file_client(path.name)
            with open(local_file_path, "wb") as local_file:
                download = file_client.download_file()
                local_file.write(download.readall())

            logger.info(f"Downloaded: {path.name} to {local_file_path}")

    def upload_folder_to_adls(
        self, local_folder_path=None, adls_folder_path=today_dashed_str_with_key()
    ):
        try:
            if local_folder_path is None:
                local_folder_path = (
                    self.config["output"]["directory"] + today_dashed_str_with_key()
                )
            adls_folder_path = self.initial_path + "/" + adls_folder_path
            logger.info(
                f"Starting to upload files from {local_folder_path} to {adls_folder_path}"
            )
            directory_client = self.service_client.get_directory_client(
                self.container_name, adls_folder_path
            )
            for root, dirs, files in os.walk(local_folder_path):
                [
                    self.process_path_to_upload(
                        directory_client, file_name, local_folder_path
                    )
                    for file_name in files
                ]
            logger.info("All Files Uploaded !")
        except Exception as e:
            logger.error(f"Unable to upload files to ADLS. Due to {e}")

    def process_path_to_upload(self, directory_client, file_name, local_folder_path):
        local_file_path = local_folder_path + "/" + file_name
        file_client = directory_client.create_file(file_name)
        # Upload the file
        with open(local_file_path, "rb") as data:
            file_client.upload_data(data, overwrite=True)
        logger.info(f"File {file_name} uploaded to ADLS Gen2.")
