from fastapi import FastAPI
from app.api.auth import auth
from app.api.projects import projects
from app.api.documents import documents
from app.infrastructure.exception_handler import register_exception_handlers


def get_application() -> FastAPI:
    app = FastAPI(
        title="Project management server",
        version="1.0.0",
        description="API for project management.",
    )
    app.include_router(auth)
    app.include_router(projects)
    app.include_router(documents)
    register_exception_handlers(app)
    return app


app = get_application()
