__version__ = "0.1.0"

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import loader
from .bot import XBot

# Bot Class
xbot = XBot()

# ASGI Server
app = FastAPI(
    title="X-API",
    description="A Multipurpose REST API.\
    \n ### Features:\
    \n - Search movies, video game and tv shows with IMDB.\
    \n - Playstore app search.\
    \n - Url Shortner.\
    \n - Paste text on Dogbin and Nekobin.\
    \n - Find latest news.\
    \n - IP Address details.\
    \n - draw_line (random crap).",
    openapi_url="/api/openapi.json",
    docs_url=None,
    redoc_url="/redoc",
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")

# Load endpoints from "/routes"
loader.load_modules()
