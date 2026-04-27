#!/bin/bash

echo "Building AdalatAI for Render..."

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Build FAISS index (important!)
python -c "from ai_engine.build_index import build_faiss_index; build_faiss_index()"

# Collect static files
python manage.py collectstatic --noinput

echo "Build completed!"