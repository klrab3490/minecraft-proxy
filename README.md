# minecraft-proxy

Exposes a [Crafty Controller](https://craftycontrol.com/) instance's Minecraft servers
to the internet over ngrok, plus a small web UI to start/stop servers and pick which
one is currently tunneled.

## Stack

- **nginx-minecraft** — reverse-proxies Crafty's web admin UI (HTTPS on `8443`) to port `80`.
- **ngrok-minecraft** — runs the ngrok agent with no static tunnel. The `ui` service opens/closes
  the actual TCP tunnel at runtime via ngrok's local API (`:4041`).
- **ui** — Flask app + single page. Lists servers from Crafty's API, starts/stops them,
  and points the one ngrok tunnel (free plan = 1 at a time) at whichever server you pick.

## Setup

1. Copy `.env.example` to `.env` and fill in:
   - `NGROK_AUTHTOKEN` — from your [ngrok dashboard](https://dashboard.ngrok.com).
   - `CRAFTY_API_TOKEN` — create in Crafty under **My Account → API Tokens**, on a role
     that has **only the `COMMANDS` permission** checked (the UI only calls
     start/stop, nothing else — leave every other permission unchecked).
   - `CRAFTY_BASE_URL` — defaults to `https://big-bear-crafty:8443/api/v2`; change the
     host if Crafty isn't reachable under that name on your `big-bear-crafty` network.
2. Make sure the external `big-bear-crafty` docker network exists (`docker network create big-bear-crafty`
   if you don't already have it from your Crafty deployment).
3. `docker compose up -d`
4. Open `http://<host>:8080` for the UI, `http://<host>` for Crafty's web admin.

## Adding a new Minecraft server

Create it in Crafty as usual, on its own port. No compose/nginx changes needed — it
shows up in the UI's server list automatically. ngrok's free plan only tunnels one
server at a time; pick which one via **Expose** in the UI.

## Building the UI image

`ui/` builds via `docker compose up --build` for local use. CI also builds and pushes
it to GHCR on every push to `main` that touches `ui/` — see
[`.github/workflows/docker-build.yml`](.github/workflows/docker-build.yml). To build
manually:

```sh
docker build -t ghcr.io/<org>/<repo>/minecraft-ui:latest ./ui
docker push ghcr.io/<org>/<repo>/minecraft-ui:latest
```

To run compose against the published image instead of building locally, swap the
`ui` service's `build: ./ui` for `image: ghcr.io/<org>/<repo>/minecraft-ui:latest`.

## Tests

```sh
cd ui
pip install -r requirements.txt
python -m unittest test_app.py -v
```
