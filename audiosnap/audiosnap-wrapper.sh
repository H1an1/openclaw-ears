#!/bin/bash
# audiosnap-wrapper: Run audiosnap via Terminal.app to inherit Screen Recording permission
# This works around macOS TCC restrictions when called from processes without screen recording access

AUDIOSNAP="/Users/han1/clawd/audiosnap/.build/release/audiosnap"
ARGS="$@"

if [ -z "$ARGS" ]; then
    ARGS="5 audiosnap-output.wav"
fi

# If we have screen recording permission, run directly
if "$AUDIOSNAP" --help >/dev/null 2>&1; then
    # Try direct first (faster)
    "$AUDIOSNAP" $ARGS 2>&1
    EXIT=$?
    if [ $EXIT -eq 0 ]; then
        exit 0
    fi
fi

# Fallback: run via Terminal.app which has screen recording permission
osascript -e "tell application \"Terminal\" to do script \"$AUDIOSNAP $ARGS; exit\"" >/dev/null 2>&1

# Wait for the output file to appear
OUTPUT=$(echo "$ARGS" | awk '{print $2}')
if [ -z "$OUTPUT" ]; then
    OUTPUT="audiosnap-output.wav"
fi

# Wait for recording to complete
DURATION=$(echo "$ARGS" | awk '{print $1}')
if [ -z "$DURATION" ]; then
    DURATION=5
fi
sleep $((DURATION + 3))

if [ -f "$OUTPUT" ]; then
    echo "✅ Done: $OUTPUT" >&2
else
    echo "❌ Recording may have failed. Check Terminal.app" >&2
    exit 1
fi
