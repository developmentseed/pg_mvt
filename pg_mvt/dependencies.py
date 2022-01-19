"""pg_mvt dependencies."""

import re
from enum import Enum

from morecantile import Tile, TileMatrixSet, tms

from pg_mvt.functions import registry as FunctionRegistry
from pg_mvt.layer import Layer, Table

from starlite import HTTPException, Parameter, Request

TileMatrixSetNames = Enum(  # type: ignore
    "TileMatrixSetNames", [(a, a) for a in sorted(tms.list())]
)


def TileMatrixSetParams(
    TileMatrixSetId: str = Parameter(
        default=TileMatrixSetNames.WebMercatorQuad.name,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    ),
) -> TileMatrixSet:
    """TileMatrixSet parameters."""
    return tms.get(TileMatrixSetId)


def TileParams(
    z: int = Parameter(ge=0, le=30, description="Tiles's zoom level"),
    x: int = Parameter(description="Tiles's column"),
    y: int = Parameter(description="Tiles's row"),
) -> Tile:
    """Tile parameters."""
    return Tile(x, y, z)


def LayerParams(
    request: Request,
    layer: str = Parameter(description="Layer Name"),
) -> Layer:
    """Return Layer Object."""
    func = FunctionRegistry.get(layer)
    if func:
        return func
    else:
        table_pattern = re.match(  # type: ignore
            r"^(?P<schema>.+)\.(?P<table>.+)$", layer
        )
        if not table_pattern:
            raise HTTPException(
                status_code=404, detail=f"Invalid Table format '{layer}'."
            )

        assert table_pattern.groupdict()["schema"]
        assert table_pattern.groupdict()["table"]

        for r in request.app.state.table_catalog:
            if r["id"] == layer:
                return Table(**r)

    raise HTTPException(status_code=404, detail=f"Table/Function '{layer}' not found.")
