"""Entry point for running the application."""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port
    )
