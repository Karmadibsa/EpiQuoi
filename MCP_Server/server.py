import uvicorn

from mcp_server.app import create_app
from mcp_server.config import get_settings

app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())