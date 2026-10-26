"""Credentialed client for one explicitly configured CP PLUS / ONVIF-compatible camera."""

from __future__ import annotations

import argparse
import getpass
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPDigestAuthHandler, HTTPPasswordMgrWithDefaultRealm, Request, build_opener


class CameraError(RuntimeError):
    """A connection, authentication, or camera response error."""


@dataclass(frozen=True)
class CameraConfig:
    """Connection settings for one camera/DVR that you are authorized to access."""

    host: str
    username: str
    password: str
    http_port: int = 80
    rtsp_port: int = 554
    channel: int = 1
    subtype: int = 0
    use_https: bool = False
    timeout_seconds: int = 10

    def __post_init__(self) -> None:
        if not self.host or "://" in self.host or "/" in self.host:
            raise ValueError("host must be a hostname or IP address without a scheme or path")
        for name, value in (("http_port", self.http_port), ("rtsp_port", self.rtsp_port)):
            if not 1 <= value <= 65535:
                raise ValueError(f"{name} must be between 1 and 65535")
        if self.channel < 1 or self.subtype not in (0, 1):
            raise ValueError("channel must be >= 1 and subtype must be 0 (main) or 1 (sub)")


class CPPlusCamera:
    """Uses CP PLUS/Dahua-compatible CGI endpoints with HTTP Digest authentication."""

    def __init__(self, config: CameraConfig):
        self.config = config
        scheme = "https" if config.use_https else "http"
        self.base_url = f"{scheme}://{config.host}:{config.http_port}"
        password_manager = HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, self.base_url, config.username, config.password)
        self.opener = build_opener(HTTPDigestAuthHandler(password_manager))

    def _get(self, path: str, query: Optional[dict[str, str]] = None) -> bytes:
        if not path.startswith("/"):
            raise ValueError("path must start with /")
        url = self.base_url + path
        if query:
            url += "?" + urlencode(query)
        request = Request(url, method="GET", headers={"User-Agent": "cplus-camera-client/1.0"})
        try:
            with self.opener.open(request, timeout=self.config.timeout_seconds) as response:
                return response.read()
        except HTTPError as error:
            if error.code in (401, 403):
                raise CameraError("camera rejected the configured credentials") from error
            raise CameraError(f"camera returned HTTP {error.code}") from error
        except URLError as error:
            raise CameraError(f"unable to reach configured camera: {error.reason}") from error

    def device_info(self) -> str:
        """Return vendor/device information from the configured camera only."""
        response = self._get("/cgi-bin/magicBox.cgi", {"action": "getSystemInfo"})
        return response.decode("utf-8", errors="replace")

    def snapshot(self) -> bytes:
        """Fetch one JPEG snapshot from the selected channel."""
        return self._get(
            "/cgi-bin/snapshot.cgi",
            {"channel": str(self.config.channel), "subtype": str(self.config.subtype)},
        )

    def rtsp_url(self) -> str:
        """Return the common CP PLUS/Dahua RTSP URL; do not print it because it contains a password."""
        user = quote(self.config.username, safe="")
        password = quote(self.config.password, safe="")
        return (
            f"rtsp://{user}:{password}@{self.config.host}:{self.config.rtsp_port}"
            f"/cam/realmonitor?channel={self.config.channel}&subtype={self.config.subtype}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Connect to one authorized CP PLUS camera or DVR.")
    parser.add_argument("--host", required=True, help="Camera/DVR hostname or IP address")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", help="Omit to enter it securely at the prompt")
    parser.add_argument("--http-port", type=int, default=80)
    parser.add_argument("--rtsp-port", type=int, default=554)
    parser.add_argument("--channel", type=int, default=1)
    parser.add_argument("--subtype", type=int, choices=(0, 1), default=0)
    parser.add_argument("--https", action="store_true")
    parser.add_argument("--device-info", action="store_true")
    parser.add_argument("--snapshot", type=Path, metavar="JPEG_PATH")
    parser.add_argument("--print-rtsp-template", action="store_true")
    args = parser.parse_args()
    if not (args.device_info or args.snapshot or args.print_rtsp_template):
        parser.error("select --device-info, --snapshot, or --print-rtsp-template")
    only_template = args.print_rtsp_template and not args.device_info and args.snapshot is None
    password = args.password if args.password is not None else ("" if only_template else getpass.getpass("Camera password: "))
    camera = CPPlusCamera(
        CameraConfig(
            host=args.host,
            username=args.username,
            password=password,
            http_port=args.http_port,
            rtsp_port=args.rtsp_port,
            channel=args.channel,
            subtype=args.subtype,
            use_https=args.https,
        )
    )
    try:
        if args.device_info:
            print(camera.device_info())
        if args.snapshot:
            args.snapshot.parent.mkdir(parents=True, exist_ok=True)
            args.snapshot.write_bytes(camera.snapshot())
            print(f"Snapshot saved to {args.snapshot}")
        if args.print_rtsp_template:
            print(
                "RTSP endpoint: "
                f"rtsp://<username>:<password>@{args.host}:{args.rtsp_port}"
                f"/cam/realmonitor?channel={args.channel}&subtype={args.subtype}"
            )
    except (CameraError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
