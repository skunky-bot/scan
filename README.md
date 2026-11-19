# Skunky Scan

V1 performs **bounded HTML parsing only**, without network retrieval or arbitrary crawling.

`POST /v1/extract` requires a non-empty `X-Skunky-Token`, with `{"source_id":"example-docs","source_url":"https://example.com/","html":"<a href='mailto:info@example.com'>Contact</a>"}`.

Extracts a bounded set of email/phone candidates and records `network_fetched=false`. The caller must enforce permitted sources. This parsing contract is not sufficient for a lawful lead collection or outreach system by itself.

Live crawling is deferred until SSRF-safe egress, robots/terms/rate limiting, provenance, security and POPIA controls are reviewed. Local: `pip install -r requirements.txt && SKUNKY_SERVICE_TOKEN=... uvicorn app:app --port 8000`.
