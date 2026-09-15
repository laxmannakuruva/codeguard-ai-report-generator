---
name: Artifact API routing collisions
description: Path-based artifact routing can collide when a generic API scaffold already owns the conventional /api prefix.
---

When a workspace already has a generic API artifact using `/api`, a new product API may return proxy errors even when its own service is healthy. Give the product API exclusive ownership of `/api` and move the unused scaffold to a distinct legacy path before smoke testing.

**Why:** The shared proxy routes by path, not by artifact intent, so duplicate `/api` registrations are ambiguous and can send requests to an unstarted or unrelated service.

**How to apply:** Check registered artifact paths before adding a backend service; keep each API path unique, restart the managed backend workflow after Python route edits, and verify through the shared proxy rather than calling the service port directly.