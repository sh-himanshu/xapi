from urllib.parse import quote, urlencode

from fastapi import Query, Request
from fastapi.responses import RedirectResponse

from .. import app, templates


@app.get("/create_preview", include_in_schema=False)
async def create_preview(
    request: Request,
    title: str,
    image: str,
    description: str,
    redirect_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
):
    if "TelegramBot" in str(request.headers.get("user-agent")):
        return templates.TemplateResponse(
            "rickroll.html",
            {
                "request": request,
                "title": title,
                "image": image,
                "description": description,
            },
        )
    return RedirectResponse(redirect_url)


@app.get("/custom_preview")
async def create_custom_webpage_preview(
    request: Request,
    title: str,
    image: str,
    description: str,
    slug: str = Query(
        "",
        title="slug",
        description="Custom Key",
        max_length=25,
    ),
    redirect_url: str = Query(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="redirect_url",
        description="",
    ),
):
    host = f"https://{request.headers.get('host')}"
    params = {
        "title": title,
        "image": image,
        "description": description,
        "redirect_url": redirect_url,
    }
    short_url = f"/short?slug={slug}&url=" + quote(
        f"{host}/create_preview?{urlencode(params)}"
    )
    return RedirectResponse(short_url)
