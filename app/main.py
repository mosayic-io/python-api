"""
You can create any API endpoints you need in this file. Mosayic abstracts away the initialization
and boilerplate code into the API's "app" variable below, allowing you to get started with ease.

Later, if you need to more control, you can access the FastAPI app instance directly, or just create your own.
"""
from mosayic import app


@app.get("/example")
async def example_route():
    return { "message": "Welcome to your Python API!" }
