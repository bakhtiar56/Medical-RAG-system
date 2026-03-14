#!/bin/sh
# Entrypoint for the Medical RAG System Docker container.
# Fails fast if OPENAI_API_KEY is not set, because the app requires it.

if [ -z "${OPENAI_API_KEY}" ]; then
    echo "ERROR: OPENAI_API_KEY is not set." >&2
    echo "Please provide it via --env-file .env or -e OPENAI_API_KEY=<your-key>." >&2
    echo "Example: docker run -p 8501:8501 --env-file .env medical-rag-system" >&2
    exit 1
fi

exec "$@"
