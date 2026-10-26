# Dashboard asset notices

The dashboard has no added Python or npm runtime dependency. The following browser assets are vendored locally so the interface does not contact a CDN during use.

- **Lucide 0.468.0:** Recognized icon library, bundled from `https://unpkg.com/lucide@0.468.0/dist/umd/lucide.min.js`. The complete upstream license is in `static/vendor/LUCIDE-LICENSE.txt`, retrieved from `https://raw.githubusercontent.com/lucide-icons/lucide/0.468.0/LICENSE`.
- **IBM Plex Sans and IBM Plex Mono:** Local WOFF2 assets from Google Fonts. The SIL Open Font License is in `static/vendor/PLEX-LICENSE.txt`; see `https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexsans/OFL.txt`.
- **Frontend design guidance:** Applied from the requested Anthropic skill, `https://github.com/anthropics/skills/tree/main/skills/frontend-design`. The skill was design guidance, not an imported runtime library.

Font asset retrieval URLs were `https://fonts.gstatic.com/s/ibmplexsans/v23/zYXzKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1syxeKYY.woff2` and `https://fonts.gstatic.com/s/ibmplexmono/v20/-F63fjptAgt5VM-kVkqdyU8n1i8q1w.woff2`. The final package manifest records the exact asset bytes and SHA-256 fingerprints.
