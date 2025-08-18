from fastapi import FastAPI
import logging

from app.api.contract import auth, projects, documents


def get_application() -> FastAPI:
    """Application factory."""

    # Configure root logger only once
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )

    app = FastAPI(
        title="Project management server",
        version="1.0.0",
        description=(
            "API for project management."
        ),
    )

    # Routes
    app.include_router(auth)
    app.include_router(projects)
    app.include_router(documents)

    return app

app = get_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 