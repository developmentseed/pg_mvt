"""pg_mvt.db: database events."""

import json
from typing import Sequence

from buildpg import asyncpg

from pg_mvt.settings import PgSettings

from starlite import Starlite

pg_settings = PgSettings()


async def table_index(db_pool: asyncpg.BuildPgPool) -> Sequence:
    """Fetch Table index."""
    async with db_pool.acquire() as conn:
        sql_query = """
            WITH geo_tables AS (
                SELECT
                    f_table_schema,
                    f_table_name,
                    f_geometry_column,
                    type,
                    srid
                FROM
                    geometry_columns
            ), t AS (
            SELECT
                f_table_schema,
                f_table_name,
                f_geometry_column,
                type,
                srid,
                jsonb_object(
                    array_agg(column_name),
                    array_agg(udt_name)
                ) as coldict,
                (
                    SELECT
                        ARRAY[
                            ST_XMin(extent.geom),
                            ST_YMin(extent.geom),
                            ST_XMax(extent.geom),
                            ST_YMax(extent.geom)
                        ]
                    FROM (
                        SELECT
                            coalesce(
                                ST_Transform(ST_SetSRID(ST_EstimatedExtent(f_table_schema, f_table_name, f_geometry_column), srid), 4326),
                                ST_MakeEnvelope(-180, -90, 180, 90, 4326)
                            ) as geom
                    ) AS extent
                ) AS bounds
            FROM
                information_schema.columns,
                geo_tables
            WHERE
                f_table_schema=table_schema
                AND
                f_table_name=table_name
            GROUP BY
                f_table_schema,
                f_table_name,
                f_geometry_column,
                type,
                srid
            )
            SELECT
                jsonb_agg(
                    jsonb_build_object(
                        'id', concat(f_table_schema, '.', f_table_name),
                        'schema', f_table_schema,
                        'table', f_table_name,
                        'geometry_column', f_geometry_column,
                        'geometry_srid', srid,
                        'geometry_type', type,
                        'properties', coldict,
                        'bounds', bounds
                    )
                )
            FROM t
            ;
        """
        q = await conn.prepare(sql_query)
        content = await q.fetchval()

    return json.loads(content)


async def connect_to_db(app: Starlite) -> None:
    """Connect."""
    app.state.pool = await asyncpg.create_pool_b(
        pg_settings.connection_string,
        min_size=pg_settings.db_min_conn_size,
        max_size=pg_settings.db_max_conn_size,
        max_queries=pg_settings.db_max_queries,
        max_inactive_connection_lifetime=pg_settings.db_max_idle,
    )
    app.state.table_catalog = await table_index(app.state.pool)


async def close_db_connection(app: Starlite) -> None:
    """Close connection."""
    await app.state.pool.close()
