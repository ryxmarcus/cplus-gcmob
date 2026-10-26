"""Local web interface for one authorized CP PLUS/Dahua camera."""

from __future__ import annotations

import html
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from cplus_camera import CameraConfig, CameraError, CPPlusCamera


def _value(form: dict[str, list[str]], name: str, default: str = "") -> str:
    return form.get(name, [default])[0].strip()


def _camera(form: dict[str, list[str]]) -> CPPlusCamera:
    return CPPlusCamera(
        CameraConfig(
            host=_value(form, "host"),
            username=_value(form, "username"),
            password=_value(form, "password"),
            http_port=int(_value(form, "http_port", "80")),
            rtsp_port=int(_value(form, "rtsp_port", "554")),
            channel=int(_value(form, "channel", "1")),
            subtype=int(_value(form, "subtype", "0")),
        )
    )


def _page(message: str = "") -> bytes:
    safe_message = html.escape(message)
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CP PLUS Camera</title>
<style>
body {{ font: 16px system-ui, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }}
label {{ display: block; margin-top: .7rem; }} input, select {{ box-sizing: border-box; padding: .45rem; width: 100%; }}
button {{ margin-top: 1rem; padding: .55rem .8rem; }} .message {{ white-space: pre-wrap; background: #f3f3f3; padding: .8rem; }}
.row {{ display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; }}
</style>
<h1>CP PLUS camera</h1>
<p>Credentials are sent only to the configured camera and are not saved by this app.</p>
<form method="post" action="/channels">
<label>Camera/NVR host <input name="host" required placeholder="192.168.1.50"></label>
<div class="row"><label>Username <input name="username" required></label>
<label>Password <input name="password" type="password" required></label></div>
<div class="row"><label>HTTP port <input name="http_port" type="number" value="80"></label>
<label>RTSP port <input name="rtsp_port" type="number" value="554"></label></div>
<button type="submit">Test connection and list channels</button>
</form>
{safe_message}
</html>""".encode("utf-8")


class CameraHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _form(self) -> dict[str, list[str]]:
        length = int(self.headers.get("Content-Length", "0"))
        return parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/":
            self._send(200, "text/html; charset=utf-8", _page())
            return
        self._send(404, "text/plain; charset=utf-8", b"Not found\n")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        form = self._form()
        try:
            camera = _camera(form)
            if path == "/channels":
                channels = [{"number": item.number, "name": item.name} for item in camera.channels()]
                message = html.escape(json.dumps(channels, indent=2))
                self._send(200, "text/html; charset=utf-8", _page(f"<h2>Channels</h2><pre class=\"message\">{message}</pre>"))
                return
            if path == "/snapshot":
                self._send(200, "image/jpeg", camera.snapshot())
                return
            self._send(404, "text/plain; charset=utf-8", b"Not found\n")
        except (CameraError, ValueError, TypeError) as error:
            self._send(400, "text/html; charset=utf-8", _page(f"<p class=\"message\">Error: {html.escape(str(error))}</p>"))

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    host = os.environ.get("CAMERA_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer((host, port), CameraHandler)
    print(f"CP PLUS camera web app listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
