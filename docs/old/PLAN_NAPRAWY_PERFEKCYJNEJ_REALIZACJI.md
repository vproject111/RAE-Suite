# 🛠️ PLAN NAPRAWY I PERFEKCYJNEGO DOMKNIĘCIA WDROŻENIA RAE-SUITE V3.0
## Krytyczny Audyt Zgodności z `docs/ITERACYJNY_PLAN_ROZWOJU_RAE.md`

**Status:** Plan w realizacji (Execution Plan)  
**Data:** 10 października 2026  
**Lokalizacja:** `/home/grzegorz/cloud/RAE-Suite/docs/PLAN_NAPRAWY_PERFEKCYJNEJ_REALIZACJI.md`  
**Cel:** Wyeliminowanie wszystkich niespójności z pierwotnym planem rozwoju i osiągnięcie 100% perfekcji inżynieryjnej.

---

## 1. WYNIKI AUDYTU (CO WYMAGAŁO NAPRAWY)

| ID | Komponent / Obszar | Niezgodność z Planem | Działanie Naprawcze |
| :--- | :--- | :--- | :--- |
| **G1** | `packages/rae-open-claw` | Folder wciąż znajdował się na dysku w `packages/` mimo jawnego nakazu usunięcia w Iteracji 0. | Całkowite usunięcie katalogu `packages/rae-open-claw`. |
| **G2** | `core/phoenix_engine.py` | Plik został zrefaktoryzowany zamiast usunięty, a stary `AutonomyKernel` nadal go importował. | Usunięcie `core/phoenix_engine.py` i uniezależnienie rdzenia od starego symulacyjnego modułu. |
| **G3** | `packages/rae-quality/src/ast_inspector.py` | Moduł zaimplementowano w `engines/testing/`, ale plan wymagał ścieżki w `src/`. | Utworzenie fasady/mostu w `packages/rae-quality/src/ast_inspector.py` re-eksportującego `ASTInspector`. |
| **G4** | `packages/rae-mcp-server/server.py` | `rae_memory_store` nie przyjmował `envelope: dict` z atrybucją `ContextEnvelope`, `rae_memory_search` wymagał listy zamiast `layer="all"`, a narzędzie sandbox miało nazwę `exec` zamiast `run`. | Rozszerzenie schematów i logiki `server.py`: obsługa `envelope`, obsługa `layer: str = "all"`, alias `rae_sandbox_run`. |
| **G5** | Konfiguracja Antigravity MCP | Pliki `~/.gemini/antigravity/mcp_config.json` i `~/.gemini/config/mcp_config.json` były puste (0 B). | Zapisanie definicji serwera `rae-suite` do obu plików konfiguracyjnych MCP agenta. |
| **G6** | Klaster: Odporność na offline Node 1 | Próba wykonania na niedostępnym Node 1 rzucała wyjątek sieciowy bez czytelnej diagnozy i fallbacku. | Implementacja w `LayerTriadRunner` graceful degradation: raport o niedostępności lokalnego GPU z sugerowanym fallbackiem do Tier 1 Flash. |
| **G7** | Autorytet Wiedzy w wyszukiwaniu MCP | Wyniki z pamięci nie uwzględniały wagi autorytetu (`authority:canonical > empirical > heuristic`). | Dodanie ważenia autorytetu w formacie odpowiedzi `rae_memory_search`. |

---

## 2. ETAPY WYKONAWCZE NAPRAWY

### Krok 1: Fizyczne wyczyszczenie długu technologicznego
- Usunięcie katalogu `packages/rae-open-claw`.
- Usunięcie pliku `core/phoenix_engine.py` i aktualizacja `core/autonomy_kernel.py`.

### Krok 2: Ujednolicenie ścieżek modułów w `rae-quality`
- Utworzenie `packages/rae-quality/src/ast_inspector.py` eksportującego `ASTInspector`.
- Weryfikacja importów testami.

### Krok 3: Dopracowanie serwera MCP (`packages/rae-mcp-server`)
- Dodanie parametru `envelope: Optional[Dict[str, Any]]` do `rae_memory_store`.
- Dodanie walidacji `ContextEnvelope` i propagacja pól `source_type`, `attribution`, `authority_level`.
- Obsługa `layer: str = "all"` w `rae_memory_search` oraz ważenie według autorytetu faktów.
- Udostępnienie narzędzia `rae_sandbox_run` obok `rae_sandbox_exec`.
- Zaktualizowanie testów jednostkowych w `packages/rae-mcp-server/tests/test_server.py`.

### Krok 4: Rejestracja w konfiguracji Antigravity / Gemini CLI
- Zapisanie poprawnego schematu MCP w `/home/grzegorz/.gemini/antigravity/mcp_config.json` oraz `/home/grzegorz/.gemini/config/mcp_config.json`.

### Krok 5: Odporność klastra na błędy sieciowe (Resilience)
- Dodanie w `LayerTriadRunner` wyłapywania `httpx.ConnectError` dla Node 1 / Node 2 z czytelnym komunikatem i wskazaniem fallbacku do Tier 1.

### Krok 6: Pełna weryfikacja regresji (100% Green Test Suite)
- Uruchomienie wszystkich pakietów testowych.
- Zapisanie kryptograficznego potwierdzenia do pamięci RAE.
