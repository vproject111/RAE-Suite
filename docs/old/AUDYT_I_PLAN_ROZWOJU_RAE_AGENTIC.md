# Rygorystyczny Audyt Architektury i Plan Rozwoju RAE-agentic (Zero-Regression Roadmap)

**Data audytu:** 10 października 2026 r.  
**Przedmiot audytu:** `packages/rae-agentic-memory` (`rae-core`, `apps/memory_api`, `rae_adapters`)  
**Metodologia:** Inspekcja kodu źródłowego, uruchomienie 1085 testów `rae-core`, weryfikacja adapterów bazodanowych PostgreSQL/Qdrant, ocena odporności na awarie.

---

## 1. Stan Faktyczny i Wyniki Testów

- **`rae-core`**: 1085 testów jednostkowych przechodzi w **16.21 s** ze statusem **100% green**.
- **Warstwa matematyczna (`rae_core/math/`)**: 145 testów w **0.54 s** bez ostrzeżeń i błędów.
- **Baza PostgreSQL**: Deterministyczny UPSERT ze zliczaniem świadków (`witness_count`) oparty o SHA-256 (`content_hash`).
- **Przestrzeń wektorowa Qdrant**: Named Vectors (384d MiniLM, 768d Ollama/Bielik, 1536d Cloud) w pełni funkcjonalne.

---

## 2. Diagnoza Wąskich Gardeł i Długu Technicznego

1. **Monolit `RAECoreService` (1 627 linii kodu w `apps/memory_api/services/rae_core_service.py`)**:
   - Klasa łączy inicjalizację adapterów, silnika, runtime, wykrywanie wzorców agentowych, twarde ramy ISO, CRUD, zanik pamięci, wsadowe odpytywanie i zarządzanie tenantami/projektami.
   - Wymaga natychmiastowej dekompozycji do wzorca Fasady (Facade Pattern) z delegatami domenowymi bez naruszenia publicznego API.

2. **Kruchość i Uzależnienie Refleksji od Zewnętrznych/Lokalnych LLM (`reflection_engine_v2.py`)**:
   - Refleksja kognitywna opiera się w 100% na modelach językowych. W przypadku przestoju Ollama lub przeciążenia sieci/LLM, proces konsolidacji rzuca błąd 500 lub blokuje kolejkę Celery.
   - Konieczne jest wdrożenie dwustopniowej refleksji: **Tier 1 (heurystyczno-grafowa i klasteryzacja gęstościowa DBSCAN/k-means za $0.00 w <5ms)** oraz **Tier 2 (synteza semantyczna LLM na żądanie)**.

3. **Brak Trybu "RAE-Embedded" dla Lekkich Agentów CLI (Antigravity, Hermes)**:
   - Korzystanie z RAE wymaga obecnie uruchomionego pełnego stosu kontenerów Docker (Postgres, Qdrant, Redis).
   - `rae-core` posiada zalążek adaptera SQLite, lecz brakuje gotowej fabryki `EmbeddedRAE` (SQLite + wektory NumPy/HNSW/sqlite-vec), która działa w jednym pliku bez Dockera.

4. **Niewykorzystana Pasywna Ingestia (Implicit Capture)**:
   - Mimo obecności automatu stanów w `runtime.py`, większość integracji wciąż opiera się na ręcznych wywołaniach narzędzi MCP `save_memory`.
   - Należy wdrożyć przezroczyste przechwytywanie operacji narzędziowych przez serwer MCP jako `Shadow Traces` do warstwy `working`.

---

## 3. Plan Rozwoju Krok po Kroku (Zero Regression)

### Faza 1: Chirurgiczna Dekompozycja `RAECoreService` (Wzorzec Facade)
- Wydzielenie delegatów w `apps/memory_api/services/delegates/`:
  - `ingestion_delegate.py` (store, SHA-256, walidacja `info_class`),
  - `retrieval_delegate.py` (query, search, reranking, fuzja),
  - `lifecycle_delegate.py` (decay, TTL, projekty, tenanty),
  - `governance_delegate.py` (hard frames, audyt ISO 42001).
- `RAECoreService` staje się 1-linijkową fasadą delegującą wywołania. Zero zmian w sygnaturach FastAPI.

### Faza 2: Dwustopniowy Silnik Refleksji (Math-First, LLM-Second)
- Implementacja Tier 1 w `rae_core/reflection/deterministic.py`:
  - Klasteryzacja kosinusowa bez LLM ($>0.92$ podobieństwa),
  - Wyliczanie macierzy współwystępowania pojęć,
  - Automatyczne scalanie duplikatów i inkrementacja `witness_count`.
- Tier 2 jako asynchroniczny proces syntezy LLM uruchamiany w tle (Node 3 / OpenRouter).

### Faza 3: RAE-Embedded (Zero-Docker Single-File Engine)
- Uzupełnienie adaptera SQLite w `rae-core/rae_core/adapters/sqlite/` o zintegrowane wyszukiwanie wektorowe (NumPy Cosine Similarity / HNSWlib).
- Udostępnienie fabryki `EmbeddedRAE.open("memory.db")` dla lokalnych agentów CLI.

### Faza 4: Pasywna Ingestia w Serwerze MCP
- Dodanie middleware w `packages/rae-mcp-server/` rejestrującego wywołania narzędziowe jako `ContextEnvelope` w warstwie `working`.
- Automatyczna okresowa konsolidacja do warstwy `episodic` i `semantic`.

---

## 4. Macierz Bezpieczeństwa Zmian

| Komponent | Dozwolona modyfikacja | Zakaz modyfikacji |
|:---|:---|:---|
| **Baza danych** | Dodanie opcjonalnych indeksów lub nowych tabel SQLite | Zmiany schematu tabeli `memories`, usuwanie kolumn, łamanie migracji |
| **Endpointy REST** | Wewnętrzne przekierowanie do delegatów | Zmiana ścieżek `/v2/memories/*`, zmiana formatu odpowiedzi JSON |
| **Matematyka (`rae_core/math`)** | Nowe heurystyki dla Tier 1 refleksji | Zmiana formuły bazowego scoringu $\alpha, \beta, \gamma$ |
| **Narzędzia MCP** | Automatyczne zbieranie śladów w tle | Zmiana nazw parametrów `rae_memory_store` / `rae_memory_search` |
