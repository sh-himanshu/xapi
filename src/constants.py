from os import getenv
from pathlib import Path


class Constants:
    def __init__(self):
        self.heroku_env = bool(getenv("DYNO"))
        config = dict(
            host="0.0.0.0" if self.heroku_env else "localhost",
            port=int(getenv("PORT", 5000)),
            dogbin="https://del.dog",
            nekobin="https://nekobin.com",
            playstore="https://play.google.com",
            imdb={
                "url": "https://www.imdb.com",
                "ttype_dict": {
                    "movie": "ft",
                    "tv": "tv",
                    "episode": "ep",
                    "game": "vg",
                },
            },
            down_path=Path("downloads"),
            ipinfo_api="https://ipinfo.io/{}?token=",
            tg_bot_api=(
                "https://api.telegram.org/bot"
                "1834586901:AAFYOTOtvfInznX6p7D3B_Hjyyap7jrulqY"
                "/sendMessage"
            ),
            tg_group_invite="http://t.me/joinchat/UiXYeQDNFmWaOLzM",
            news_feed="https://news.google.com/rss/search?q=",
            imgur_api="https://api.imgur.com/3/image?client_id=",
            mongodb_uri="",
            tg_game_api="https://tbot.xyz/api/setScore",
        )
        for key, value in config.items():
            setattr(self, key, value or None)

        # Create Download Dir.
        self.down_path.mkdir(exist_ok=True)
