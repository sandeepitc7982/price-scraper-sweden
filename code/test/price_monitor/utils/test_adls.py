import unittest
from unittest.mock import patch, call, Mock

from src.price_monitor.utils.adls import AzureDataLakeStorage
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)


class TestAzureDataLakeStorage(unittest.TestCase):

    @patch.object(AzureDataLakeStorage, "initialize_datalake_client")
    @patch.object(AzureDataLakeStorage, "authenticate_with_service_principal")
    @patch("src.price_monitor.utils.adls.dbutils")
    def test_initialization_of_adls_should_authenticate(
        self,
        mock_dbutils,
        mock_authenticate_with_service_principal,
        mock_initialize_datalake_client,
    ):
        config = {
            "output": {
                "directory": "data/",
            },
            "adls": {
                "enabled": True,
                "scope_type": "credential",
                "tenant_id": "TENANT-ID",
                "service_client_id": "CLIENT_ID",
                "service_secret": "SERVICE_SECRET",
                "storage_account_name": "STORAGE_ACCOUNT_NAME",
                "container_name": "CONTAINER_NAME",
                "initial_path": "INITIAL_PATH",
            },
        }
        mock_dbutils.secrets.get.side_effect = [
            "tenant",
            "client",
            "secret",
            "account",
            "container",
            "initial",
        ]

        AzureDataLakeStorage(config)
        mock_dbutils.secrets.get.assert_has_calls(
            calls=[
                call(scope="credential", key="TENANT-ID"),
                call(scope="credential", key="CLIENT_ID"),
                call(scope="credential", key="SERVICE_SECRET"),
                call(scope="credential", key="STORAGE_ACCOUNT_NAME"),
                call(scope="credential", key="CONTAINER_NAME"),
                call(scope="credential", key="INITIAL_PATH"),
            ]
        )
        mock_authenticate_with_service_principal.assert_called_with(
            "tenant", "client", "secret"
        )
        mock_initialize_datalake_client.assert_called_with("account")

    @patch("src.price_monitor.utils.adls.dbutils")
    def test_upload_folder_to_directory_should_upload_to_given_directory(
        self, mock_dbutils
    ):
        config = {
            "output": {
                "directory": "data/",
            },
            "adls": {
                "enabled": True,
                "scope_type": "credential",
                "tenant_id": "TENANT-ID",
                "service_client_id": "CLIENT_ID",
                "service_secret": "SERVICE_SECRET",
                "storage_account_name": "STORAGE_ACCOUNT_NAME",
                "container_name": "CONTAINER_NAME",
                "initial_path": "INITIAL_PATH",
            },
        }
        mock_dbutils.secrets.get.side_effect = [
            "tenant",
            "client",
            "secret",
            "account",
            "container",
            "initial",
        ]

        adls = AzureDataLakeStorage(config)
        mock_service_client = Mock()
        setattr(adls, "service_client", mock_service_client)
        adls.upload_folder_to_adls()
        mock_service_client.get_directory_client.assert_called_with(
            "container", f"initial/{today_dashed_str_with_key()}"
        )

    @patch("src.price_monitor.utils.adls.dbutils")
    def test_download_folder_from_directory_should_download_to_given_directory(
        self, mock_dbutils
    ):
        config = {
            "output": {
                "directory": "data/",
            },
            "adls": {
                "enabled": True,
                "scope_type": "credential",
                "tenant_id": "TENANT-ID",
                "service_client_id": "CLIENT_ID",
                "service_secret": "SERVICE_SECRET",
                "storage_account_name": "STORAGE_ACCOUNT_NAME",
                "container_name": "CONTAINER_NAME",
                "initial_path": "INITIAL_PATH",
            },
        }
        mock_dbutils.secrets.get.side_effect = [
            "tenant",
            "client",
            "secret",
            "account",
            "container",
            "initial",
        ]

        adls = AzureDataLakeStorage(config)
        mock_service_client = Mock()
        setattr(adls, "service_client", mock_service_client)
        mock_file_system_client = Mock()
        mock_file_system_client.get_paths.return_value = []
        mock_service_client.get_file_system_client.return_value = (
            mock_file_system_client
        )
        adls.download_folder_from_adls()
        mock_service_client.get_file_system_client.assert_called_with("container")
        mock_file_system_client.get_paths.assert_called_with(
            path=f"initial/{yesterday_dashed_str_with_key()}"
        )
