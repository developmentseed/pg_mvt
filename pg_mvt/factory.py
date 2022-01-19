"""pg_mvt.factory: router factories."""

import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from urllib.parse import urlencode

from morecantile import Tile, TileMatrixSet

from pg_mvt.dependencies import (
    LayerParams,
    TileMatrixSetNames,
    TileMatrixSetParams,
    TileParams,
)
from pg_mvt.functions import registry as FunctionRegistry
from pg_mvt.layer import Function, Layer, Table
from pg_mvt.models.mapbox import TileJSON
from pg_mvt.models.OGC import TileMatrixSetList

from starlite import Parameter, Provide, Request, controller, get

from starlette.datastructures import QueryParams, URLPath
from starlette.routing import NoMatchFound, compile_path
from starlette.templating import Jinja2Templates

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore


def queryparams_to_kwargs(q: QueryParams, ignore_keys: List = []) -> Dict:
    """Convert query params to dict."""
    keys = list(q.keys())
    values = {}
    for k in keys:
        if k in ignore_keys:
            continue

        v = q.getlist(k)
        values[k] = v if len(v) > 1 else v[0]

    return values


def replace_params(
    path: str,
    path_params: Dict[str, str],
) -> Tuple[str, dict]:
    """convert endpoint path.

    Modified version of https://github.com/encode/starlette/blob/05d531483a37f1d4e023eece13dd801daba5e818/starlette/routing.py#L88-L99
    """
    for key, value in list(path_params.items()):
        if "{" + key + "}" in path:
            path = path.replace("{" + key + "}", value)
            path_params.pop(key)

    return path, path_params


class Controller(controller.Controller):
    """Custom controller class."""

    def url_for(self, request: Request, name: str, **path_params: Any) -> str:
        """Return full url (with prefix) for a specific endpoint."""
        url_path = self.url_path_for(name, **path_params)

        base_url = str(request.base_url)
        if self.path:
            base_url += self.path.lstrip("/")

        return url_path.make_absolute_url(base_url=base_url)

    def url_path_for(self, name: str, **path_params: Any) -> URLPath:
        """return path for a controller handler."""
        for route in self.get_route_handlers():
            path_regex, path_format, param_convertors = compile_path(route.path)
            try:
                seen_params = set(path_params.keys())
                expected_params = set(param_convertors.keys())

                if name != route.fn.__name__ or seen_params != expected_params:
                    raise NoMatchFound()

                path, remaining_params = replace_params(path_format, path_params)
                assert not remaining_params
                return URLPath(path=path, protocol="http")
            except NoMatchFound:
                pass

        raise NoMatchFound()


class TilerEndpoints(Controller):
    """Tiler endpoints."""

    path = ""

    dependencies = {
        "layer": Provide(LayerParams),
        "tms": Provide(TileMatrixSetParams),
    }

    @classmethod
    def factory(
        cls,
        prefix: str = "",
        tms_dependency: Callable = None,
        layer_dependency: Callable = None,
    ) -> Type["TilerEndpoints"]:
        """Edit TilerEndpoints class."""
        new_deps = {}
        if tms_dependency:
            new_deps["tms"] = Provide(tms_dependency)
        if layer_dependency:
            new_deps["layer"] = Provide(layer_dependency)

        return type(
            "TilerEndpoints",
            (cls,),
            {"path": prefix, "dependencies": {**cls.dependencies, **new_deps}},
        )

    @get(
        path="/tiles/{layer:str}/{z:int}/{x:int}/{y:int}.pbf",
        dependencies={"tile": Provide(TileParams)},
        media_type="application/x-protobuf",
    )
    # @get(
    #     path="/tiles/{TileMatrixSetId:str}/{layer:str}/{z:int}/{x:int}/{y:int}.pbf",
    #     dependencies={"tile": Provide(TileParams)},
    #     media_type="application/x-protobuf",
    # )
    async def tile(
        self,
        request: Request,
        tms: TileMatrixSet,
        layer: Layer,
        tile: Tile,
    ) -> bytes:
        """Return vector tile."""
        pool = request.app.state.pool

        kwargs = queryparams_to_kwargs(
            request.query_params, ignore_keys=["tilematrixsetid"]
        )
        content = await layer.get_tile(pool, tile, tms, **kwargs)

        return bytes(content)

    @get(path="/{layer:str}/tilejson.json")
    # @get(path="/{TileMatrixSetId:str}/{layer:str}/tilejson.json")
    async def tilejson(
        self,
        request: Request,
        tms: TileMatrixSet,
        layer: Layer,
        minzoom: Optional[int] = Parameter(
            required=False, description="Overwrite default minzoom."
        ),
        maxzoom: Optional[int] = Parameter(
            required=False, description="Overwrite default maxzoom."
        ),
    ) -> TileJSON:
        """Return TileJSON document."""
        path_params: Dict[str, Any] = {
            # "TileMatrixSetId": tms.identifier,
            "layer": layer.id,
            "z": "{z}",
            "x": "{x}",
            "y": "{y}",
        }
        tile_endpoint = self.url_for(request, "tile", **path_params)

        # qs_key_to_remove = ["tilematrixsetid", "minzoom", "maxzoom"]
        qs_key_to_remove = ["minzoom", "maxzoom"]
        query_params = [
            (key, value)
            for (key, value) in request.query_params._list
            if key.lower() not in qs_key_to_remove
        ]

        if query_params:
            tile_endpoint += f"?{urlencode(query_params)}"

        minzoom = minzoom if minzoom is not None else (layer.minzoom or tms.minzoom)
        maxzoom = maxzoom if maxzoom is not None else (layer.maxzoom or tms.maxzoom)

        return TileJSON(
            **{
                "minzoom": minzoom,
                "maxzoom": maxzoom,
                "name": layer.id,
                "bounds": layer.bounds,
                "tiles": [tile_endpoint],
            }
        )

    @get(path="/tables.json")
    async def tables_index(self, request: Request) -> List[Table]:
        """Index of tables."""

        def _get_tiles_url(id: str) -> str:
            try:
                return self.url_for(
                    request, "tile", layer=id, z="{z}", x="{x}", y="{y}"
                )
            except NoMatchFound:
                return None

        return [
            Table(**r, tileurl=_get_tiles_url(r["id"]))
            for r in request.app.state.table_catalog
        ]

    @get(path="/table/{layer:str}.json")
    async def table_metadata(self, request: Request, layer: Layer) -> Table:
        """Return table metadata."""

        def _get_tiles_url(id) -> str:
            try:
                return self.url_for(
                    request, "tile", layer=id, z="{z}", x="{x}", y="{y}"
                )
            except NoMatchFound:
                return None

        layer.tileurl = _get_tiles_url(layer.id)
        return Table(**layer.dict(by_alias=True))

    @get(path="/functions.json")
    async def functions_index(self, request: Request) -> List[Function]:
        """Index of functions."""

        def _get_tiles_url(id: str) -> str:
            try:
                return self.url_for(
                    request, "tile", layer=id, z="{z}", x="{x}", y="{y}"
                )
            except NoMatchFound:
                return None

        return [
            Function(**func.dict(exclude_none=True), tileurl=_get_tiles_url(id))
            for id, func in FunctionRegistry.funcs.items()
        ]

    @get(path="/function/{layer:str}.json")
    async def function_metadata(self, request: Request, layer: Layer) -> Function:
        """Return function metadata."""

        def _get_tiles_url(id) -> str:
            try:
                return self.url_for(
                    request, "tile", layer=id, z="{z}", x="{x}", y="{y}"
                )
            except NoMatchFound:
                return None

        layer.tileurl = _get_tiles_url(layer.id)
        # TODO: exclude sql in response
        return Function(**layer.dict(by_alias=True))

    @get(path="/{layer:str}/viewer")
    async def viewer(self, request: Request, layer: Layer) -> str:
        """Viewer."""
        tile_url = self.url_for(request, "tilejson", layer=layer.id)

        return templates.TemplateResponse(  # type: ignore
            name="viewer.html",
            context={"endpoint": tile_url, "request": request},
            media_type="text/html",
        )


class TMSEndpoints(Controller):
    """TileMatrixSets endpoints."""

    path = ""

    dependencies = {
        "tms": Provide(TileMatrixSetParams),
    }

    supported_tms: Type[TileMatrixSetNames] = TileMatrixSetNames

    @classmethod
    def factory(
        cls,
        prefix: str = "",
        tms_dependency: Callable = None,
        supported_tms: Type[TileMatrixSetNames] = None,
    ) -> Type["TMSEndpoints"]:
        """Edit TMSEndpoints class."""
        new_deps = {}
        if tms_dependency:
            new_deps["tms"] = Provide(tms_dependency)

        return type(
            "TMSEndpoints",
            (cls,),
            {
                "path": prefix,
                "dependencies": {**TMSEndpoints.dependencies, **new_deps},
                "supported_tms": supported_tms or TMSEndpoints.supported_tms,
            },
        )

    @get(path="/tileMatrixSets")
    def TileMatrixSet_list(self, request: Request) -> TileMatrixSetList:
        """
        Return list of supported TileMatrixSets.

        Specs: http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
        """
        return TileMatrixSetList(
            **{
                "tileMatrixSets": [
                    {
                        "id": _tms.name,
                        "title": _tms.name,
                        "links": [
                            {
                                "href": self.url_for(
                                    request,
                                    "TileMatrixSet_info",
                                    TileMatrixSetId=_tms.name,
                                ),
                                "rel": "item",
                                "type": "application/json",
                            }
                        ],
                    }
                    for _tms in self.supported_tms
                ]
            }
        )

    # TODO: can't use openapi with TileMatrixSet
    @get(path="/tileMatrixSets/{TileMatrixSetId:str}")
    def TileMatrixSet_info(self, tms: TileMatrixSet) -> Dict:
        """Return TileMatrixSet JSON document."""
        # TODO: returning Dict is not enough because there are models within the model
        # we will need to iterate through all items
        return json.loads(tms.json(exclude_none=True))
