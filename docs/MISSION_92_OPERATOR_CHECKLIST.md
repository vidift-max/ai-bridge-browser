# Mission 92 — Operator Checklist

## Before approval

- Confirm Blueprint plan is Free.
- Confirm no persistent disk is planned.
- Confirm auto-sync remains disabled until explicitly desired.
- Confirm only MESSENGER_TOKEN_AI_A and MESSENGER_TOKEN_AI_B are manual secrets.
- Confirm no payment-dependent resource was added.

## After explicit approval

- Record the Render service ID.
- Record the deployment ID.
- Record the deployed commit SHA.
- Record the generated public staging URL.
- Run scripts/verify_staging_http.py against that URL.
- Do not paste credentials into logs, reports, or chat.

## Controlled browser test

1. Admin opens /rooms.
2. Admin creates a room-scoped invitation.
3. Second browser opens the invitation link.
4. Guest submits the join request.
5. Admin approves the request.
6. Guest enters the room.
7. AI-01 sends one text message to AI-02.
8. AI-02 acknowledges the message.
9. Admin revokes the invitation.
10. A fresh redemption attempt is rejected.

## Evidence record

Record timestamp, staging URL, service ID, deployment ID, commit SHA, health result, readiness result, invite result, message/ACK result, and revoke/redeem result. Do not treat a local emulator pass as proof of a live Render deployment.
