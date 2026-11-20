# Navigation Controller

Navigation is a future separation seam around WebView loading.

Responsibilities: validate requested URL, start navigation, expose loading/readiness/error state, and avoid delivering queued actions until readiness.

It must not execute remote commands.