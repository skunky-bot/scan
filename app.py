"""Bounded HTML extraction. No outbound network calls or crawling."""
from __future__ import annotations

import hmac
import os
import re
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, HttpUrl

app = FastAPI(title="Skunky Scan", version="0.1.0")
EMAIL = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)
PHONE = re.compile(r"(?<!\w)(?:\+\d{1,3}[\s().-]?)?(?:\d[\s().-]?){7,14}\d(?!\w)")


def authorize(token: str | None = Header(default=None, alias="X-Skunky-Token")) -> None:
    expected = os.environ.get("SKUNKY_SERVICE_TOKEN", "")
    if not expected or token is None or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Service authentication required")


class ExtractRequest(BaseModel):
    source_id: str = Field(min_length=1, max_length=100)
    source_url: HttpUrl
    html: str = Field(min_length=1, max_length=200_000)


class ContactParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []
        self.skipped = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template"}:
            self.skipped += 1
        if tag == "a" and not self.skipped:
            href = dict(attrs).get("href", "")
            if href.startswith(("mailto:", "tel:")):
                self.links.append(unquote(href.split("?", 1)[0]))

    def handle_endtag(self, tag):
        if tag in {"script", "style", "template"}:
            self.skipped = max(0, self.skipped - 1)

    def handle_data(self, data):
        if not self.skipped:
            self.parts.append(data)


@app.get("/healthz")
def health():
    return {"status": "ok", "service": "scan"}


@app.post("/v1/extract", dependencies=[Depends(authorize)])
def extract(body: ExtractRequest):
    parser = ContactParser()
    parser.feed(body.html)
    material = " ".join(parser.parts + parser.links)
    emails = sorted({e.lower() for e in EMAIL.findall(material)})[:25]
    phones = sorted({p.strip() for p in PHONE.findall(material)})[:25]
    return {
        "source_id": body.source_id,
        "source_url": str(body.source_url),
        "emails": emails,
        "phones": phones,
        "provenance": "caller-supplied-html",
        "network_fetched": False,
    }
