from datetime import datetime
from typing import Any, Dict, Optional

from fastapi.responses import UJSONResponse

from .. import app, xbot


@app.get("/paste", response_class=UJSONResponse)
async def paste(
    text: str,
    dogbin: bool = True,
    nekobin: bool = False,
    title: Optional[str] = None,
    author: Optional[str] = None,
    ext: str = "txt",
) -> Dict[str, Any]:
    dogbin_uri = xbot.config.dogbin
    nekobin_uri = xbot.config.nekobin
    out = {
        "date": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        "content": text,
        "length": len(text),
    }
    if dogbin:
        async with xbot.http.post(
            f"{dogbin_uri}/documents", data=text.encode("utf-8")
        ) as resp:
            if resp.status == 200:
                d_json = await resp.json()
                key = d_json.get("key")
                link = f"{dogbin_uri}/{key}.{ext}"
                is_url = d_json.get("isUrl")
                out["dogbin"] = {
                    "raw": f"{dogbin_uri}/raw/{key}",
                    "is_url": is_url,
                    "link": f"{dogbin_uri}/v/{key}" if is_url else link,
                    "redirect": link if is_url else None,
                }
            else:
                out["dogbin"] = {
                    "error": f"Failed to reach '{dogbin_uri}'",
                    "status_code": resp.status,
                }
    if nekobin:
        async with xbot.http.post(
            f"{nekobin_uri}/api/documents",
            json={"content": text, "title": title, "author": author},
        ) as resp:
            if resp.status == 201:
                n_json = await resp.json()
                if n_json.get("ok"):
                    key = n_json["result"].get("key")
                    out["nekobin"] = {
                        "raw": f"{nekobin_uri}/raw/{key}",
                        "link": f"{nekobin_uri}/{key}.{ext}",
                        "author": n_json["result"].get("author"),
                        "title": n_json["result"].get("title"),
                    }
            else:
                out["nekobin"] = {
                    "error": f"Failed to reach '{nekobin_uri}'",
                    "status_code": resp.status,
                }

    return out
