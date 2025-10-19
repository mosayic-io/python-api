from mosayic import app
from fastapi.responses import HTMLResponse

from app.core.settings import get_settings
from app.services.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <html>
        <body>
            <h1>The Python API</h1>
            <p>This is the API root. If you're in the development environment, visit <a href="/docs">/docs</a> to see the available
            endpoints.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
