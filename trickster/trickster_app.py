"""Trickster application."""

import uvicorn
from fastapi import FastAPI

from trickster.endpoints import internal, mocked
from trickster.config import get_config
from trickster.meta import get_metadata
from trickster.openapi import OpenApiSpec
from trickster.router import get_router
from trickster.logger import get_logger


def load_openapi_routes() -> None:
    """Load OpenApi and configure all routes."""
    logger = get_logger()
    if spec_path := get_config().openapi_boostrap:
        try:
            spec = OpenApiSpec.load(spec_path)
            get_router().routes = spec.get_routes()
            logger.warning(f'Loaded OpenApi specification "{spec_path}".')
        except FileNotFoundError:
            logger.warning(f'OpenApi specification "{spec_path}" was not loaded.')


def create_app() -> FastAPI:
    """Create and initialize Trickster application."""
    config = get_config()
    metadata = get_metadata()
    app = FastAPI(
        title=metadata.name,
        version=metadata.version,
        description=metadata.description,
        docs_url=f'{config.internal_prefix}/docs'
    )
    app.include_router(internal.router, prefix=config.internal_prefix)
    app.include_router(mocked.router)

    load_openapi_routes()
    return app


def main() -> None:
    """Run Trickster application."""
    app = create_app()
    uvicorn.run(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
