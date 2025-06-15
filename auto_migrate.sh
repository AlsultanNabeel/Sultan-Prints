#!/bin/bash

set -e

# Activate virtual environment if needed (uncomment if you use venv)
# source venv/bin/activate

# Run Flask database migrations
export FLASK_APP=manage.py

echo "🔄 Running database migrations (flask db upgrade)..."
flask db upgrade

echo "✅ Database migrations complete!" 