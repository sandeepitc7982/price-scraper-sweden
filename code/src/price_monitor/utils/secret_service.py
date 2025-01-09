from google.cloud import secretmanager
from loguru import logger

SECRET_PREFIX = "SECRET::"


def fetch_secret_if_present(secret: str) -> str:
    if secret.startswith(SECRET_PREFIX):
        secret_name = secret[len(SECRET_PREFIX) :]
        logger.debug("Retrieving secret from secret manager")
        client = secretmanager.SecretManagerServiceClient()

        return client.access_secret_version(name=secret_name).payload.data.decode(
            "UTF-8"
        )
    else:
        logger.debug("Using raw secret value")
        return secret
