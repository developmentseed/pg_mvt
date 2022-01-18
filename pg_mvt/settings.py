"""pg_mvt config."""

from functools import lru_cache
from typing import Optional

from starlite import CORSConfig

import pydantic


class _APISettings(pydantic.BaseSettings):
    """API settings"""

    name: str = "PgMVT"
    cors_origins: str = "*"
    cachecontrol: str = "public, max-age=3600"

    @pydantic.validator("cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    class Config:
        """model config"""

        env_prefix = "PG_MVT_"
        env_file = ".env"

    @property
    def cors_config(self) -> Optional[CORSConfig]:
        if self.cors_origins:
            return CORSConfig(allow_origins=self.cors_origins)

        return None


@lru_cache()
def APISettings() -> _APISettings:
    """This function returns a cached instance of the Settings object."""
    return _APISettings()


class _PgSettings(pydantic.BaseSettings):
    """Postgres-specific API settings."""

    database_url: pydantic.PostgresDsn

    # see https://www.psycopg.org/psycopg3/docs/api/pool.html#the-connectionpool-class for options
    db_min_conn_size: int = 1  # The minimum number of connection the pool will hold
    db_max_conn_size: int = 10  # The maximum number of connections the pool will hold

    db_max_queries: int = (
        50000  # Maximum number of requests that can be queued to the pool
    )
    db_max_idle: float = 300  # Maximum time, in seconds, that a connection can stay unused in the pool before being closed, and the pool shrunk.

    class Config:
        """model config"""

        env_prefix = "PG_MVT_"
        env_file = ".env"

    @property
    def connection_string(self):
        """Create reader psql connection string."""
        return self.database_url


@lru_cache()
def PgSettings() -> _PgSettings:
    """Postgres Settings."""
    return _PgSettings()


class _TileSettings(pydantic.BaseSettings):
    """Tile settings."""

    tile_resolution: int = 4096
    tile_buffer: int = 256
    max_features_per_tile: int = 10000
    default_minzoom: int = 0
    default_maxzoom: int = 22

    class Config:
        """model config"""

        env_prefix = "PG_MVT_"
        env_file = ".env"


@lru_cache()
def TileSettings() -> _TileSettings:
    """Tile Settings."""
    return _TileSettings()
