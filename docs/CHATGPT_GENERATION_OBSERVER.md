# ChatGPT generation indicator observation

The browser uses the visible ChatGPT stop-generation control (the blue square shown while an answer is being generated) as its primary completion signal.

## Read-only observation contract

- A visible stop control is observed as GENERATING.
- NOT_GENERATING is only meaningful when a chat composer is also visible.
- UNKNOWN is returned when the page is not in a recognizable chat state or the observation script fails.
- The initial absence of the stop control is never treated as completion.
- Completion requires a prior GENERATING observation followed by two consecutive NOT_GENERATING observations. An UNKNOWN observation resets that consecutive-absence counter.
- If generation becomes visible again, the state returns to RESPONDING.

The observer checks semantic UI signals (button accessible label and/or test id), not button color or a fixed pixel position. This is more resilient to themes and layout changes while still targeting the blue square stop-generation control the user described.

## Boundaries

This slice is a tested state machine and a read-only WebView observation script. It does not click Stop, send messages, read response text, inspect context fullness, or claim that the selector has been validated against a live ChatGPT page. ChatGPT can change its UI; if no known signal is found, the state remains UNKNOWN rather than falsely completing a mission. Runtime integration and physical-device validation remain pending.
