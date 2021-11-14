from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import app

templates = Jinja2Templates(directory="templates/")


@app.get("/", include_in_schema=False)
async def read_root():
    return RedirectResponse(url="/docs")


@app.get("/docs", include_in_schema=False)
async def the_docs_url_page_web_plugin_func_swagger():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " docs",
    )
