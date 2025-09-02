import argparse
import uvicorn

from app.config import Settings, Secrets
from app.logger.logger import logger


def resolve_env(dev: bool) -> str:
    if dev:
        return "development"
    return "production"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dev", action="store_true", help="Tryb developerski")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port serwera")
    args = parser.parse_args()

    app_env = resolve_env(args.dev)

    secrets = Secrets()

    import app.config

    app.config.settings = Settings(app_env=app_env, secrets=secrets)

    settings = app.config.settings
    logger.info(
        f"🚀 Starting server in {settings.app_env} mode (DB={settings.database_url})"
    )

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=args.port,
        reload=settings.is_development,
        access_log=True,
    )


if __name__ == "__main__":
    main()
