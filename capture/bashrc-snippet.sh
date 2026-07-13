# claude-sessions capture wrapper
# Not yet sourced from ~/.bashrc — add manually once reviewed.
# Wraps every new interactive shell in `script -t`, capturing both the
# typescript (raw bytes) and a timing file, so scriptreplay works for free
# and reader/render.py has what it needs for a readable transcript.
if [ -z "$CLAUDE_SESSIONS_ACTIVE" ] && [ -n "$PS1" ]; then
    export CLAUDE_SESSIONS_ACTIVE=1
    mkdir -p ~/claude-sessions/raw
    session_id="$(date +%Y%m%d-%H%M%S)-$$"
    exec script --quiet --flush --return --command="$SHELL" \
        --log-timing="$HOME/claude-sessions/raw/${session_id}.timing" \
        "$HOME/claude-sessions/raw/${session_id}.typescript"
fi
