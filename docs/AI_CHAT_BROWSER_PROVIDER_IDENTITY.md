# Mission 15 — Provider Identity Registry & First Authorized Connector

## Ten rounds
1. Audited Mission 14 and Mission 13 pull requests; both remain open and unmerged.
2. Reviewed official provider documentation: OpenAI API uses API credentials and server-side bearer authentication; this is distinct from a ChatGPT consumer-account session.
3. Confirmed the repository already contains a server-side OpenAI Responses adapter and authenticated GPT-6 routes; avoided duplicating the connector.
4. Created an isolated Mission 15 branch based on Mission 14.
5. Added a provider registry for OpenAI, Anthropic Claude API and Google Gemini API.
6. Made provider identity explicit: project API credential, Console API credential, or developer API credential; these are not consumer account sessions.
7. Added honest states: configured does not mean connected; OpenAI remains CONFIGURED_UNVERIFIED until a real successful request is observed.
8. Added an authenticated provider catalog endpoint and tightened GPT-6 status semantics so configured credentials do not make the AI appear online.
9. Added deterministic tests for provider states, unsupported providers, and credential-value non-disclosure.
10. Added dedicated backend CI and documentation with the operational activation boundary.

## Provider feasibility result
- OpenAI: an existing server-side Responses API adapter is implemented. It requires a separately provisioned OpenAI API credential; a ChatGPT subscription/session is not the same credential. The catalog reports only whether the server has a configured key, not whether the key is valid or the service is reachable.
- Anthropic Claude: official Claude API access requires a Claude Console API key or a supported workload identity flow. This repository does not yet implement that connector.
- Google Gemini: official Gemini API supports developer API credentials and OAuth flows depending on product. This repository does not yet implement that connector.
- No browser scraping, cookie access, login automation, CAPTCHA/2FA bypass, or consumer account impersonation is supported.

## API
Authenticated `GET /v1/providers` returns a safe catalog. It never returns secret values.
Existing authenticated `POST /v1/gpt6/respond` remains the OpenAI API message path. A successful response proves that one request completed; it does not create a persistent ChatGPT web session or a permanent online presence.

## Activation boundary
No API key was supplied or activated in this mission. No paid API request was made. No real provider connectivity is claimed. To test a live connector later, an authorized server-side credential must be provisioned by the user and a single request must be explicitly approved, since API usage may incur charges.

## Validation
`python -m unittest discover -s server -p 'test_*.py' -v`
