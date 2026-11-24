#!/bin/sh
# Reinicia o banco de demonstração para o estado inicial (dados fictícios).
# Pensado para um cron diário na máquina que hospeda a demo (ex.: VM no Proxmox):
#
#   0 4 * * *  cd /opt/crm-operacional && ./scripts/reset_demo.sh >> /var/log/crm-demo-reset.log 2>&1
#
# Como funciona:
#   1. apaga /dados/checklist.db* DENTRO do container em execução (banco, -wal e -shm);
#   2. recria o banco com "flask db upgrade", o catálogo e o seed de demonstração;
#   3. reinicia o serviço, para o gunicorn abrir o banco novo (AUTO_SEED_DEMO=1 no
#      docker-compose.demo.yml torna a subida idempotente: nada duplica).
#
# A pilha precisa estar rodando com docker-compose.yml (e, para a demo pública,
# com docker-compose.demo.yml junto — ver README).

set -eu

# Pasta do projeto (este script mora em scripts/).
cd "$(dirname "$0")/.."

SERVICO=crm-checklist

if ! docker compose ps --status running --quiet "$SERVICO" | grep -q .; then
    echo "ERRO: o serviço $SERVICO não está rodando. Suba a pilha antes de resetar a demonstração."
    exit 1
fi

echo "[$(date '+%d/%m/%Y %H:%M:%S')] Apagando o banco de demonstração dentro do container..."
docker compose exec -T "$SERVICO" sh -c 'rm -f /dados/checklist.db /dados/checklist.db-wal /dados/checklist.db-shm'

echo "[$(date '+%d/%m/%Y %H:%M:%S')] Recriando o banco (migrações + catálogo + seed de demonstração)..."
docker compose exec -T "$SERVICO" sh -c 'python -m flask db upgrade && python -m flask catalogo carregar && python -m flask seed-demo'

echo "[$(date '+%d/%m/%Y %H:%M:%S')] Reiniciando o serviço para servir o banco novo..."
docker compose restart "$SERVICO" >/dev/null

echo "[$(date '+%d/%m/%Y %H:%M:%S')] Demonstração reiniciada: banco limpo e populado com os dados fictícios."
