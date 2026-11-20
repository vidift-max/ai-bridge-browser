# AI Guest Invitation

An invitation creates an authorized participation record, not control over the external service.

Fields:
- AI_ID
- PROVIDER
- SESSION_ID
- ROOM_ID
- MISSION_ID
- INVITED_AT
- ACCEPTED_AT
- STATUS
- LAST_SEEN
- EXIT_REQUESTED

Disconnected or rate-limited guests retain pending mission state. The coordinator decides whether to wait, retry, or reassign.
