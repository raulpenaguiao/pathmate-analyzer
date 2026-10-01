---
from: mirror
to: smith
subject: Raul wants the demo portal online now (Cloudflare quick tunnel)
timestamp: 260929083119
---
Raul (09-29) is on remote access and wants to try the chat (the EngineV1 test). :8010 is **not running** right now; I checked and got no response.

Please:
1. Relaunch the demo portal as on 09-25: throwaway DATA_DIR, 0925 export attached, login raul / chat-demo.
2. Expose it with a **Cloudflare quick tunnel**. Raul chose this over Tailscale and SSH. cloudflared isn't installed, so use the user-local binary from GitHub releases (no sudo): `cloudflared tunnel --url http://localhost:8010`.
3. PushNotification Raul the trycloudflare URL, and stop the tunnel when he's done.

Note: the URL is public, so the login is the only guard. Keep it on throwaway data only, never the real data/.
