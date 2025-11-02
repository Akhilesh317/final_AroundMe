#!/bin/bash

# Backup script for Around Me data

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="aroundme_backup_$TIMESTAMP"

echo "================================================"
echo "Around Me - Backup Script"
echo "================================================"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Creating backup: $BACKUP_NAME"
echo ""

# Backup Postgres
echo "Backing up PostgreSQL database..."
docker compose -f deploy/compose.yml exec -T postgres pg_dump -U aroundme aroundme > "$BACKUP_DIR/${BACKUP_NAME}_postgres.sql"
echo "✓ Database backup: $BACKUP_DIR/${BACKUP_NAME}_postgres.sql"

# Backup Redis (optional, since it's cache)
echo "Backing up Redis cache..."
docker compose -f deploy/compose.yml exec -T redis redis-cli --rdb /data/dump.rdb SAVE > /dev/null 2>&1
docker cp aroundme-redis:/data/dump.rdb "$BACKUP_DIR/${BACKUP_NAME}_redis.rdb" 2>/dev/null || echo "Note: Redis backup skipped (cache only)"

# Backup environment file (without sensitive data)
echo "Backing up configuration..."
if [ -f .env ]; then
    grep -v -E '(API_KEY|PASSWORD|SECRET)' .env > "$BACKUP_DIR/${BACKUP_NAME}_config.env" || true
    echo "✓ Config backup: $BACKUP_DIR/${BACKUP_NAME}_config.env"
fi

# Create archive
echo ""
echo "Creating compressed archive..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" ${BACKUP_NAME}_* 2>/dev/null || true
rm -f ${BACKUP_NAME}_* 2>/dev/null || true
cd ..

BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)

echo ""
echo "================================================"
echo "Backup Complete!"
echo "================================================"
echo "Location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "Size: $BACKUP_SIZE"
echo ""
echo "To restore this backup:"
echo "  ./scripts/restore.sh $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo ""

# Optional: Clean up old backups (keep last 7 days)
find "$BACKUP_DIR" -name "aroundme_backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true