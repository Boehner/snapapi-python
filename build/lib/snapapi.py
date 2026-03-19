"""
SnapAPI Python SDK
==================
A minimal, zero-dependency Python client for the SnapAPI web intelligence API.
Uses only the Python standard library (urllib, json, os).

Install:
    pip install snapapi-python
    # or: python setup.py install

Usage:
    from snapapi import SnapAPI

    client = SnapAPI()                        # reads SNAPAPI_KEY from env
    # or
    client = SnapAPI(api_key="snap_xxxxxxxx") # explicit key

    png_bytes  = client.screenshot("https://github.com")
    metadata   = client.metadata("https://github.com")
    analysis   = client.analyze("https://github.com", screenshot=True)
    pdf_bytes  = client.pdf("https://github.com", format="A4")
    img_bytes  = client.render("<h1>Hello</h1>", width=1200, height=630)
    results    = client.batch(["https://a.com", "https://b.com"])

Docs: https://snapapi.tech/docs
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

__version__ = "0.1.1"
__all__ = ["SnapAPI", "SnapAPIError"]

_BASE_URL = "https://snapapi.tech"


class SnapAPIError(Exception):
    """Raised when the SnapAPI returns an error response."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(f"SnapAPI error {status}: {message}")


class SnapAPI:
    """
    Client for the SnapAPI web intelligence API.

    Parameters
    ----------
    api_key : str, optional
        Your SnapAPI API key.  If omitted, the value of the
        ``SNAPAPI_KEY`` environment variable is used.
    base_url : str, optional
        Override the default API base URL (useful for self-hosted installs).
    timeout : int, optional
        Request timeout in seconds.  Defaults to 45.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = _BASE_URL,
        timeout: int = 45,
    ) -> None:
        self._api_key = api_key or os.environ.get("SNAPAPI_KEY", "")
        if not self._api_key:
            raise SnapAPIError(
                0,
                "No API key provided.  Set SNAPAPI_KEY env var or pass api_key= to SnapAPI().\n"
                "Get a free key at https://snapapi.tech",
            )
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get(self, path: str, params: Dict[str, Any]) -> bytes:
        """Make a GET request; return raw response bytes."""
        qs = urllib.parse.urlencode(
            {k: str(v) for k, v in params.items() if v is not None}
        )
        url = f"{self._base_url}{path}?{qs}"
        req = urllib.request.Request(url, headers={"x-api-key": self._api_key})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                msg = json.loads(body).get("error", body)
            except Exception:
                msg = body
            raise SnapAPIError(exc.code, msg) from exc

    def _get_json(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a GET request; parse and return JSON dict."""
        raw = self._get(path, params)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SnapAPIError(0, f"Invalid JSON response: {raw[:200]}") from exc

    def _post_json(self, path: str, payload: Dict[str, Any]) -> bytes:
        """Make a POST request with a JSON body; return raw response bytes."""
        body = json.dumps(payload).encode("utf-8")
        url = f"{self._base_url}{path}"
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "x-api-key": self._api_key,
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            body_str = exc.read().decode("utf-8", errors="replace")
            try:
                msg = json.loads(body_str).get("error", body_str)
            except Exception:
                msg = body_str
            raise SnapAPIError(exc.code, msg) from exc

    # ── Public API ────────────────────────────────────────────────────────────

    def screenshot(
        self,
        url: str,
        *,
        format: str = "png",
        width: int = 1280,
        height: int = 800,
        full_page: bool = False,
        dark_mode: bool = False,
        device: Optional[str] = None,
        selector: Optional[str] = None,
        delay: Optional[int] = None,
    ) -> bytes:
        """
        Capture a screenshot of *url*.

        Parameters
        ----------
        url : str
            The page to capture.
        format : str
            Output format: ``"png"``, ``"jpeg"``, or ``"webp"``.
        width : int
            Viewport width in pixels.
        height : int
            Viewport height in pixels.
        full_page : bool
            Capture the full scrollable page.
        dark_mode : bool
            Render with ``prefers-color-scheme: dark``.
        device : str, optional
            Device preset, e.g. ``"iphone14"``, ``"pixel7"``, ``"ipad"``.
        selector : str, optional
            CSS selector — capture only that element.
        delay : int, optional
            Extra milliseconds to wait before capturing.

        Returns
        -------
        bytes
            Raw image bytes (PNG/JPEG/WebP).
        """
        params: Dict[str, Any] = dict(
            url=url,
            format=format,
            width=width,
            height=height,
            full_page=str(full_page).lower(),
            dark_mode=str(dark_mode).lower(),
        )
        if device is not None:
            params["device"] = device
        if selector is not None:
            params["selector"] = selector
        if delay is not None:
            params["delay"] = delay

        return self._get("/v1/screenshot", params)

    def metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract metadata from *url*.

        Returns a dict with keys:
        ``url``, ``title``, ``description``, ``og_title``, ``og_description``,
        ``og_image``, ``og_type``, ``favicon``, ``canonical``, ``language``.

        Parameters
        ----------
        url : str
            The page to extract metadata from.

        Returns
        -------
        dict
        """
        return self._get_json("/v1/metadata", {"url": url})

    def analyze(
        self,
        url: str,
        *,
        screenshot: bool = False,
    ) -> Dict[str, Any]:
        """
        Full page analysis of *url*.

        Returns page_type, primary_cta, nav_items, technologies, word_count,
        load_time_ms, OG metadata, and (optionally) a base64 screenshot.

        Parameters
        ----------
        url : str
            The page to analyze.
        screenshot : bool
            Include a base64-encoded screenshot in the response.

        Returns
        -------
        dict
        """
        params: Dict[str, Any] = {"url": url}
        if screenshot:
            params["screenshot"] = "true"
        return self._get_json("/v1/analyze", params)

    def pdf(
        self,
        url: str,
        *,
        format: str = "A4",
        landscape: bool = False,
        margin_top: int = 20,
        margin_bottom: int = 20,
        margin_left: int = 20,
        margin_right: int = 20,
        print_background: bool = True,
        scale: float = 1.0,
        delay: Optional[int] = None,
    ) -> bytes:
        """
        Convert *url* to a PDF.

        Parameters
        ----------
        url : str
            The page to convert.
        format : str
            Paper format: ``"A4"``, ``"Letter"``, ``"A3"``, ``"A5"``, ``"Legal"``.
        landscape : bool
            Landscape orientation.
        margin_top / margin_bottom / margin_left / margin_right : int
            Margins in pixels.
        print_background : bool
            Print CSS background colors and images.
        scale : float
            Page scale (0.1–2.0).
        delay : int, optional
            Extra milliseconds to wait before generating.

        Returns
        -------
        bytes
            Raw PDF bytes.
        """
        params: Dict[str, Any] = dict(
            url=url,
            format=format,
            landscape=str(landscape).lower(),
            margin_top=margin_top,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right,
            print_background=str(print_background).lower(),
            scale=scale,
        )
        if delay is not None:
            params["delay"] = delay
        return self._get("/v1/pdf", params)

    def render(
        self,
        html: str,
        *,
        width: int = 1200,
        height: int = 630,
        format: str = "png",
    ) -> bytes:
        """
        Render raw *html* to a pixel-perfect image.

        Ideal for OG cards, email previews, certificate images.

        Parameters
        ----------
        html : str
            Full HTML string to render.
        width : int
            Viewport width in pixels.
        height : int
            Viewport height in pixels.
        format : str
            Output format: ``"png"``, ``"jpeg"``, or ``"webp"``.

        Returns
        -------
        bytes
            Raw image bytes.
        """
        payload = {"html": html, "width": width, "height": height, "format": format}
        return self._post_json("/v1/render", payload)

    def batch(
        self,
        urls: List[str],
        *,
        endpoint: str = "screenshot",
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process multiple URLs in parallel.

        Parameters
        ----------
        urls : list[str]
            List of URLs to process.
        endpoint : str
            Which endpoint to call per URL: ``"screenshot"``, ``"metadata"``,
            or ``"analyze"``.
        params : dict, optional
            Extra parameters to pass to each per-URL call.

        Returns
        -------
        list[dict]
            One result dict per URL.  Each has ``status`` (``"ok"`` or
            ``"error"``), ``url``, and endpoint-specific fields.

        Raises
        ------
        SnapAPIError
            If the batch request itself fails (not per-URL errors).
        """
        payload: Dict[str, Any] = {
            "urls": urls,
            "endpoint": endpoint,
        }
        if params:
            payload["params"] = params

        raw = self._post_json("/v1/batch", payload)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SnapAPIError(0, f"Invalid JSON in batch response: {raw[:200]}") from exc

        return data.get("results", [])


# ── CLI / demo ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("SnapAPI Python SDK — demo\n")

    client = SnapAPI()  # requires SNAPAPI_KEY in environment

    target = sys.argv[1] if len(sys.argv) > 1 else "https://github.com"

    # 1. Screenshot
    print(f"[1] Screenshot of {target}...")
    png = client.screenshot(target, full_page=False)
    with open("demo_screenshot.png", "wb") as f:
        f.write(png)
    print(f"    Saved demo_screenshot.png ({len(png) // 1024} KB)")

    # 2. Metadata
    print(f"\n[2] Metadata for {target}...")
    meta = client.metadata(target)
    print(f"    Title:    {meta.get('title', '')[:60]}")
    print(f"    OG image: {meta.get('og_image', '(none)')[:80]}")

    # 3. Analyze
    print(f"\n[3] Page analysis for {target}...")
    analysis = client.analyze(target)
    print(f"    Page type:   {analysis.get('page_type', '')}")
    print(f"    Primary CTA: {analysis.get('primary_cta', '')}")
    print(f"    Tech stack:  {', '.join(analysis.get('technologies', []))}")

    # 4. PDF
    print(f"\n[4] PDF of {target}...")
    pdf = client.pdf(target, format="A4")
    with open("demo.pdf", "wb") as f:
        f.write(pdf)
    print(f"    Saved demo.pdf ({len(pdf) // 1024} KB)")

    # 5. Render HTML → image
    print("\n[5] Render HTML to PNG...")
    html = """
    <div style="background:#1a1a2e;color:#f0f0f4;font-family:sans-serif;
                padding:80px;width:1200px;height:630px;
                display:flex;align-items:center;font-size:48px;font-weight:800;">
      Hello from SnapAPI Python SDK
    </div>"""
    img = client.render(html, width=1200, height=630)
    with open("demo_render.png", "wb") as f:
        f.write(img)
    print(f"    Saved demo_render.png ({len(img) // 1024} KB)")

    # 6. Batch
    print(f"\n[6] Batch metadata for 2 URLs...")
    results = client.batch(
        ["https://github.com", "https://example.com"],
        endpoint="metadata",
    )
    for r in results:
        status = r.get("status", "?")
        title  = r.get("title", "")[:50]
        print(f"    {status:5s}  {r.get('url', '')}  →  {title}")

    print("\nDone. Check the generated files.")
