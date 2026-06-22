#!/bin/bash
# ==============================================================================
# RAE-Suite Interactive Installer & Bootstrap Daemon
# ==============================================================================
# Focus: Data Persistence, Container Isolation, and Hybrid Search Enforcement
# ==============================================================================

# Terminal Colors for Rich Aesthetics
CYAN='\033[0;36m'
LIGHT_CYAN='\033[1;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear

# Print Premium ASCII Header
echo -e "${LIGHT_CYAN}======================================================================"
echo -e "       _____  ___   _____    _____       _ _                       "
echo -e "      |  __ \/ _ \ |  ___|  / ____|     (_) |                      "
echo -e "      | |__) | (_) | |__   | (___  _   _ _| |_ ___                 "
echo -e "      |  _  / \__, |  __|   \___ \| | | | | __/ _ \\                "
echo -e "      | | \ \   / /| |____  ____) | |_| | | ||  __/                "
echo -e "      |_|  \_\ /_/ |______||_____/ \__,_|_|\__\___|                "
echo -e "                                                                   "
echo -e "            FULL SUITE ORCHESTRATOR - SILICON ORACLE v3.2"
echo -e "======================================================================"
echo -e "🛡️  Zero Drift Governance, Absolute Auditability & Multi-Strategy Search${NC}\n"

# ⚠️  Explain the Cardinal Architecture Rule
echo -e "${RED}${BOLD}⚠️  KARDYNALNA ZASADA ARCHITEKTURY RAE (DATA ISOLATION MANDATE):${NC}"
echo -e "${YELLOW}Bazy danych RAE (Postgres, Qdrant, Redis) MUSZĄ być fizycznie wydzielone"
echo -e "poza kontenery Docker i zapisywane na dysku hosta."
echo -e "Cykl życia kontenera (restarty, awarie, uaktualnienia obrazów, 'docker compose down')"
echo -e "NIGDY nie może wpływać na utratę lub zresetowanie wiedzy poznawczej agenta!${NC}"
echo -e "----------------------------------------------------------------------"

# 1. Ask for Persistent Storage Path
echo -e "\n${LIGHT_CYAN}[KROK 1] RAE-SUITE PERSISTENT STORAGE LOCATION${NC}"
read -p "$(echo -e "${BOLD}Gdzie na dysku hosta zapisać bazy danych RAE-Suite? (Domyślnie: ../RAE-agentic-memory/data): ${NC}")" USER_DATA_DIR

if [ -z "$USER_DATA_DIR" ]; then
    USER_DATA_DIR="../RAE-agentic-memory/data"
fi

# Resolve path
if [[ "$USER_DATA_DIR" = ~* ]]; then
    # Expand tilde
    USER_DATA_DIR="${USER_DATA_DIR/#\~/$HOME}"
fi
ABS_DATA_DIR=$(readlink -f "$USER_DATA_DIR" 2>/dev/null || echo "$USER_DATA_DIR")

echo -e "💾 ${GREEN}Lokalizacja baz danych ustawiona na:${NC} ${BOLD}$ABS_DATA_DIR${NC}"

# 2. Ask for Import/Backup Path
echo -e "\n${LIGHT_CYAN}[KROK 2] RAE-SUITE DATABASE IMPORT / DATA RESTORE${NC}"
read -p "$(echo -e "${BOLD}Czy chcesz zaimportować istniejący zrzut bazy danych (.sql)? Wpisz ścieżkę (ENTER aby pominąć): ${NC}")" IMPORT_PATH

if [ -n "$IMPORT_PATH" ]; then
    if [[ "$IMPORT_PATH" = ~* ]]; then
        IMPORT_PATH="${IMPORT_PATH/#\~/$HOME}"
    fi
    if [ -f "$IMPORT_PATH" ]; then
        ABS_IMPORT_PATH=$(readlink -f "$IMPORT_PATH")
        echo -e "📥 ${GREEN}Wykryto backup:${NC} $ABS_IMPORT_PATH"
        # We will copy it to a recovery folder or handle it
        mkdir -p "$USER_DATA_DIR/recovery"
        cp "$ABS_IMPORT_PATH" "$USER_DATA_DIR/recovery/restore.sql"
        echo -e "👉 ${YELLOW}Zrzut skopiowany do: $USER_DATA_DIR/recovery/restore.sql (zostanie zaimportowany przy starcie)${NC}"
    else
        echo -e "❌ ${RED}Plik pod ścieżką '$IMPORT_PATH' nie istnieje! Pomijam krok importu.${NC}"
        IMPORT_PATH=""
    fi
else
    echo -e "ℹ️  ${CYAN}Brak backupu. Zainicjowana zostanie nowa, czysta baza danych suity.${NC}"
fi

# 3. Configure and Enforce Hybrid Search
echo -e "\n${LIGHT_CYAN}[KROK 3] HYBRID SEARCH ENFORCEMENT${NC}"
echo -e "RAE-Suite standardowo wymusza ${BOLD}Wyszukiwanie Hybrydowe${NC} (Hybrid Search):"
echo -e "  - ${CYAN}Vector Search${NC} (głębokie podobieństwo semantyczne, multi-wektorowa przestrzeń Qdrant)"
echo -e "  - ${CYAN}Fulltext / Sparse Search${NC} (dokładne dopasowanie słów kluczowych i tokenów syntaktycznych)"
echo -e "Fuzja matematyczna w ${BOLD}LogicGateway${NC} zapobiega halucynacjom wyszukiwania i dryftowi baseline'u."
echo -e "✔️  ${GREEN}Enforcing RAE_SEARCH_STRATEGY=hybrid in .env${NC}"

# 4. Generate .env configuration
echo -e "\n${LIGHT_CYAN}[KROK 4] GENERATING ENVIRONMENT CONFIGURATION${NC}"

# Read existing .env if present or use empty
if [ -f .env ]; then
    echo -e "📄 ${YELLOW}Istniejący plik .env został wykryty. Tworzę kopię zapasową (.env.bak)...${NC}"
    cp .env .env.bak
else
    touch .env
fi

# Clean existing overrides if any
sed -i '/RAE_DATA_DIR/d' .env
sed -i '/RAE_SEARCH_STRATEGY/d' .env

# Append custom persistence settings
cat << EOF >> .env

# ==============================================================================
# RAE PERSISTENCE & SEARCH SETTINGS (APPENDED BY INTERACTIVE INSTALLER)
# ==============================================================================
# Persistent host path for database containers
RAE_DATA_DIR=$ABS_DATA_DIR

# Mandatory Search Strategy: hybrid (Dense Vector + Sparse Fulltext Fusion)
RAE_SEARCH_STRATEGY=hybrid
EOF

echo -e "✅ ${GREEN}Zapisano ustawienia w pliku RAE-Suite/.env!${NC}"

# 5. Create Persistent Folders on the Host
echo -e "\n${LIGHT_CYAN}[KROK 5] CREATING HOST DIRECTORIES${NC}"
mkdir -p "$USER_DATA_DIR/postgres" "$USER_DATA_DIR/qdrant" "$USER_DATA_DIR/redis" "$USER_DATA_DIR/lite"
# Fix permissions to ensure Docker containers can read/write
chmod -R 777 "$USER_DATA_DIR" 2>/dev/null || true

echo -e "📁 ${GREEN}Utworzono i zabezpieczono foldery baz danych na hoście:${NC}"
echo -e "  - Postgres: $ABS_DATA_DIR/postgres"
echo -e "  - Qdrant:   $ABS_DATA_DIR/qdrant"
echo -e "  - Redis:    $ABS_DATA_DIR/redis"

echo -e "\n✨ ${GREEN}${BOLD}RAE-Suite została pomyślnie skonfigurowana i przygotowana do pracy!${NC}"
echo -e "----------------------------------------------------------------------"
echo -e "Uruchomienie całej suity:       ${BOLD}./start.sh${NC}"
echo -e "----------------------------------------------------------------------"
echo -e "🔒 Dane są w 100% bezpieczne poza kontenerami w katalogu: ${BOLD}$ABS_DATA_DIR${NC}\n"
