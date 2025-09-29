#!/usr/bin/env bash
# Entry point for container: wait for DB (if configured) then exec the CMD
set -e

# wait for postgres if DATABASE_URL provided and host/port parseable
if [[ -n "$DATABASE_URL" ]]; then
  # extract host and port naively
  proto_removed=${DATABASE_URL#*://}
  hostport=${proto_removed#*@}
  hostport=${hostport%%/*}
  host=${hostport%%:*}
  port=${hostport#*:}
  if [[ "$host" != "$hostport" && -n "$host" && -n "$port" ]]; then
    echo "Waiting for database $host:$port..."
    for i in {1..30}; do
      if nc -z "$host" "$port"; then
        echo "Postgres is up"
        break
      fi
      sleep 1
    done
  fi
fi

# If the project exposes a session mount at /data/session, but no files are
# present, print a friendly hint so users know how to produce/copy session
# files. This is intentionally informational only — the container will continue
# to start so it can still be used without sessions.
if [[ -d "/data/session" ]]; then
  shopt -s nullglob
  files=(/data/session/*)
  shopt -u nullglob
  if [[ ${#files[@]} -eq 0 ]]; then
    cat <<'EOF'

IMPORTANT: no Instaloader session files found in the mounted folder /data/session.

If you want the app to use an existing Instaloader session (so it is "logged in"
and can fetch private stories), create/copy the session file(s) named like:

  session-<your_username>

into the project directory on your host at ./sessions (the compose mount),
for example:

  # run locally (on your host) from the project root to generate session files
  python instaloader/2FA_bypass/import_chrome_session.py

  # then copy any generated session-<username> files into ./sessions
  mkdir -p sessions
  cp session-* sessions/

Alternatively, run the import script inside a container or generate the session
using the upstream Instaloader CLI (eg. `instaloader -l <username>`). After
placing session files into ./sessions, restart the container so they are
imported at startup.

If you intentionally don't want sessions, you can ignore this message.

EOF
  fi
fi

# execute the container command
exec "$@"
