"""pg_mvt app."""

from typing import Dict

from pg_mvt.db import close_db_connection, connect_to_db
from pg_mvt.factory import TilerEndpoints, TMSEndpoints
from pg_mvt.middleware import CacheControlMiddleware
from pg_mvt.settings import APISettings
from pg_mvt.version import __version__ as pg_mvt_version

from starlite import MediaType, OpenAPIConfig, Request, Starlite, get

from starlette.middleware import Middleware
from starlette.templating import Jinja2Templates
from starlette_cramjam.middleware import CompressionMiddleware

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    from importlib_resources import files as resources_files  # type: ignore


settings = APISettings()

templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore


@get(path="/", media_type=MediaType.HTML, include_in_schema=False)
def index(request: Request) -> str:
    """DEMO."""
    return templates.TemplateResponse(
        name="index.html",
        context={"index": request.app.state.table_catalog, "request": request},
        media_type="text/html",
    )


@get(path="/healthz", description="Health Check", tags=["Health Check"])
def ping() -> Dict:
    """Health check."""
    return {"ping": "pong!"}


app = Starlite(
    route_handlers=[
        index,
        ping,
        TilerEndpoints,
        TMSEndpoints,
    ],
    middleware=[
        Middleware(
            CacheControlMiddleware,
            cachecontrol=settings.cachecontrol,
            exclude_path={r"/healthz"},
        ),
        Middleware(CompressionMiddleware, minimum_size=0),
    ],
    cors_config=settings.cors_config,
    openapi_config=OpenAPIConfig(
        title=settings.name,
        version=pg_mvt_version,
    ),
)


# Register Start/Stop application event handler to setup/stop the database connection
@app.asgi_router.on_event("startup")
async def startup_event():
    """Application startup: register the database connection and create table list."""
    await connect_to_db(app)


@app.asgi_router.on_event("shutdown")
async def shutdown_event():
    """Application shutdown: de-register the database connection."""
    await close_db_connection(app)
