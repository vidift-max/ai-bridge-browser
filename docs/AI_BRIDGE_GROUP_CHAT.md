# AI Bridge — Group Chat

The group chat is a durable room, not a direct peer-to-peer socket between providers.

A message may target the whole room or a selected set of participants. The bridge stores one canonical message and creates delivery state per recipient.

This allows one AI to be temporarily unavailable without blocking the rest of the team.

The coordinator can later request structured turns or missions, but ordinary chat remains available for human and AI collaboration.