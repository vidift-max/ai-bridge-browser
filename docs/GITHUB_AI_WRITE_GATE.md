# GitHub AI Write Gate

Preferred flow:

AI -> authorized bridge -> scoped workspace -> Git commit -> CI -> GPT-6 review

The scope identifies permitted paths and mission purpose. Secrets, credentials, workflow administration, and unrelated project areas remain outside the AI write scope unless explicitly authorized.

Prefer short-lived, least-privilege credentials or an intermediary service over a broad personal token.
