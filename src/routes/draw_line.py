from fastapi.responses import PlainTextResponse

from .. import app


@app.get("/draw_line", response_class=PlainTextResponse)
async def draw_line(
    text: str,
    line_char: str = "-",
    line_out: str = "#",
    line_in: str = "",
    max_length: int = 38,
    reverse: bool = True,
) -> str:
    def mirror(input_str: str) -> str:
        text_chars = list(input_str)[::-1] if reverse else list(input_str)
        for i, char in enumerate(text_chars):
            for br in ["<>", "()", r"{}", "[]", "/\\"]:
                if char in br:
                    text_chars[i] = br[1 if char == br[0] else 0]
        return "".join(text_chars)

    line_length = max_length - len(text)
    line_left = round(line_length / 2)
    line_right = line_length - line_left
    line = (
        line_out,
        line_char * line_left,
        line_in,
        text,
        mirror(line_in),
        line_char * line_right,
        mirror(line_out),
    )
    return " ".join(line)
