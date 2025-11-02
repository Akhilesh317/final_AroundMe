#!/bin/bash

# Restore script for Around Me data

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore.sh <backup_file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/*.tar.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"
RESTORE_DIR="./restore_temp"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "================================================"
echo "Around Me - Restore Script"
echo "================================================"
echo ""
echo "Backup file: $BACKUP_FILE"
echo ""
echo "WARNING: This will replace existing data!"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Extract backup
echo ""
echo "Extracting backup..."
mkdir -p "$RESTORE_DIR"
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

# Restore Postgres
echo "Restoring PostgreSQL database..."
if [ -f "$RESTORE_DIR"/*_postgres.sql ]; then
    # Drop and recreate database
    docker compose -f deploy/compose.yml exec -T postgres psql -U aroundme -d postgres -c "DROP DATABASE IF EXISTS aroundme;"
    docker compose -f deploy/compose.yml exec -T postgres psql -U aroundme -d postgres -c "CREATE DATABASE aroundme;"
    
    # Restore data
    docker compose -f deploy/compose.yml exec -T postgres psql -U aroundme -d aroundme < "$RESTORE_DIR"/*_postgres.sql
    echo "✓ Database restored"
else
    echo "⚠ No database backup found in archive"
fi

# Restore Redis (optional)
echo "Restoring Redis cache..."
if [ -f "$RESTORE_DIR"/*_redis.rdb ]; then
    docker compose -f deploy/compose.yml stop redis
    docker cp "$RESTORE_DIR"/*_redis.rdb aroundme-redis:/data/dump.rdb
    docker compose -f deploy/compose.yml start redis
    echo "✓ Redis cache restored"
else
    echo "⚠ No Redis backup found in archive (cache will be empty)"
fi

# Cleanup
rm -rf "$RESTORE_DIR"

echo ""
echo "================================================"
echo "Restore Complete!"
echo "================================================"
echo ""
echo "Services may need to restart:"
echo "  docker compose -f deploy/compose.yml restart"
echo ""