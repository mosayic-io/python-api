"""
The API that uvicorn serves (`app.main:app`). Everything is assembled by
create_app() in `app/factory.py`: add endpoints as routers in `app/routes/`
and register them there.
"""
from app.factory import create_app

app = create_app()
