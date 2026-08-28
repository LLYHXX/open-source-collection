import time

import structlog
from clickhouse_driver import Client, errors

from tfc.settings import settings

logger = structlog.get_logger(__name__)


class ClickHouseClientSingleton:
    _instance = None
    _client = None

    # def __new__(cls):
    #     if cls._instance is None:
    #         cls._instance = super(ClickHouseClientSingleton, cls).__new__(cls)
    #         cls._instance.initialize_client()
    #     return cls._instance

    def __init__(self) -> None:
        self.initialize_client()

    def initialize_client(self):
        # Your connection setup here with timeouts
        self._client = Client(
            host=settings.CLICKHOUSE["CH_HOST"],
            port=settings.CLICKHOUSE["CH_PORT"],
            user=settings.CLICKHOUSE["CH_USERNAME"],
            password=settings.CLICKHOUSE["CH_PASSWORD"],
            database=settings.CLICKHOUSE["CH_DATABASE"],
        )

    @property
    def client(self):
        # Health check before returning the client
        if not self.is_connection_alive():
            self.reconnect()
        return self._client
        # return self._instance.client

    def is_connection_alive(self):
        try:
            # You can use a basic query as a health check
            if not self._client:
                return False
            start_time = time.time()
            self._client.execute("SELECT 1")
            end_time = time.time()
            logger.debug(
                "Health check query execution time: %.3f seconds", end_time - start_time
            )
            return True
        except errors.NetworkError:
            return False

    def reconnect(self):
        attempts = 3
        for _ in range(attempts):
            try:
                self.initialize_client()
                return
            except errors.NetworkError:
                time.sleep(1)  # Wait for a second before retrying
        raise ConnectionError(
            "Could not reconnect to ClickHouse after multiple attempts"
        )

    def execute(self, query, params=None):
        logger.debug("Executing query %s", query)
        logger.debug("Params of query %s", params)
        start_time = time.time()
        try:
            if not self._client:
                self.initialize_client()
            result = self._client.execute(query, params)
            end_time = time.time()
            logger.debug("Query execution time: %.3f seconds", end_time - start_time)
            return result
        except errors.NetworkError as e:
            # Handle connection error, try to reconnect and re-execute the query
            self.reconnect()
            if not self._client:
                raise ConnectionError(
                    "Failed to establish ClickHouse connection"
                ) from e
            result = self._client.execute(query, params)
            end_time = time.time()
            logger.debug(
                "Query execution time (after reconnect): %.3f seconds",
                end_time - start_time,
            )
            return result
        except Exception as e:
            # Handle or log other exceptions if necessary
            end_time = time.time()
            logger.exception("Exception while executing query %s", query)
            logger.debug("Params of query %s", params)
            logger.debug(
                "Query execution time (failed): %.3f seconds", end_time - start_time
            )
            raise e

    def close(self):
        """Close the ClickHouse connection"""
        if self._client:
            try:
                self._client.disconnect()
            except Exception as e:
                logger.warning(f"Error while closing ClickHouse connection: {e}")
            finally:
                self._client = None

    def __del__(self):
        """Ensure connection is closed when object is destroyed"""
        self.close()

    def execute_paginated(self, query, params=None, page=1, page_size=10):
        offset = (page - 1) * page_size
        paginated_query = f"{query} LIMIT {page_size} OFFSET {offset}"

        # Get the total count
        count_query = f"SELECT count() FROM ({query})"
        total_records = self._client.execute(count_query, params)[0][0]
        total_pages = -(-total_records // page_size)  # Ceiling division

        try:
            result = self._client.execute(paginated_query, params)
            return result, total_pages
        except errors.NetworkError:
            # Handle connection error, try to reconnect and re-execute the query
            self.reconnect()
            result = self._client.execute(paginated_query, params)
            return result, total_pages
        except Exception as e:
            # Handle or log other exceptions if necessary
            raise e
