# 🛡️ PLAN NAPRAWY I OSIĄGNIĘCIA PERFEKCJI INŻYNIERYJNEJ RAE V3.0
## Krytyczny Audyt Jakości, Usunięcie Wąskich Gardeł i Pełne Domknięcie Architektury

**Data audytu:** 10 października 2026 r.  
**Lokalizacja:** `/home/grzegorz/cloud/RAE-Suite/docs/PLAN_NAPRAWY_I_PERFEKCJI_V3.md`  
**Przedmiot:** `packages/rae-agentic-memory`, `packages/rae-mcp-server`, `packages/rae-phoenix`, `packages/rae-quality`, `packages/rae-hive`  
**Cel:** Wykrycie i bezwzględne usunięcie wszelkich niedoskonałości, asymetrii portów, brakujących metod w fasadach oraz zapewnienie pełnej automatyzacji konsolidacji pamięci pasywnej (Zero Drift, Zero Regression).

---

## 1. WYNIKI GŁĘBOKIEGO AUDYTU (IDENTYFIKACJA LUK I NIEDOSKONAŁOŚCI)

Mimo osiągnięcia statusu 100% green dla 1 096 testów jednostkowych `rae-core` oraz 14 testów serwera MCP, dogłębna analiza wykazała 5 obszarów wymagających dopracowania do stanu perfekcji:

| ID | Obszar / Komponent | Stan Wykryty | Ryzyko / Konsekwencja | Rozwiązanie Naprawcze |
|:---|:---|:---|:---|:---|
| **GAP-1** | **Port API w `rae-mcp-server`** | Domyślna wartość `RAE_API_URL` to `http://localhost:8001`, podczas gdy żywa instancja RAE na laptopie działa na porcie `8000` (`curl http://localhost:8001` zwraca *Connection refused*). | Wywołania MCP `call_tool` i pasywny interceptor bez jawnego podania zmiennej środowiskowej próbują uderzać pod martwy port 8001. | Ujednolicenie domyślnego portu na `http://localhost:8000` z adaptacyjnym wykrywaniem portu w `server.py`, `interceptor.py` i `mcp_config.json`. |
| **GAP-2** | **Brak automatycznej auto-konsolidacji** | W `interceptor.py` metoda `consolidate_traces` istnieje, lecz wymagała dotąd ręcznego wywołania narzędzia `rae_consolidate_traces`. | Ślady wykonania w warstwie `working` kumulują się bez samoczynnej syntezy do warstwy wiedzy `episodic`. | Wdrożenie automatycznego wyzwalacza w tle po zgromadzeniu zadanej liczby śladów (`auto_consolidate_interval = 20`). |
| **GAP-3** | **Ergonomia `EmbeddedRAE`** | `EmbeddedRAE` posiadał metody `store()`, `query()`, `search_evidence()`, `consolidate()`, ale brakowało mu bezpośrednich metod `get()`, `delete()`, `list()`. | Agent CLI (Antigravity / Hermes) musiał bezpośrednio odwoływać się do wewnętrznego `rae.storage.get_memory()`. | Dodanie bezpośrednich metod `get(memory_id)`, `delete(memory_id)`, `list(layer=...)` na poziomie fasady `EmbeddedRAE` wraz z testami. |
| **GAP-4** | **Stabilność testów w `rae-phoenix`** | Test `test_enhanced_rae_client.py` mockował `feniks.config.settings.settings` zamiast przestrzeni nazw klienta, a `test_e2e_pipeline.py` wymagał obecności `node` w systemie. | Fałszywe błędy w środowiskach bez zainstalowanego binarium `node` lub przy izolowanym module konfiguracji. | Poprawa ścieżki patchowania w `test_enhanced_rae_client.py` oraz dodanie sprawdzania `shutil.which("node")` z bezpiecznym `pytest.skip`. |
| **GAP-5** | **Czystość podmodułów Git** | Podmoduły `packages/rae-phoenix`, `packages/rae-quality` i `packages/rae-hive` zawierały drobne niezacommitowane poprawki kontraktów. | Ostrzeżenia bramki Git Gatekeeper o "dirty submodule" przy operacjach na repozytorium głównym. | Zatwierdzenie i uporządkowanie commitów w podmodułach na gałęziach funkcyjnych. |

---

## 2. PLAN POPRAWY KROK PO KROKU (REALIZACJA)

### Krok 1: Ujednolicenie i adaptacja portu API RAE (GAP-1)
- W `packages/rae-mcp-server/server.py`:
  - `RAE_API_URL = os.getenv("RAE_API_URL", "http://localhost:8000")`.
- W `packages/rae-mcp-server/interceptor.py`:
  - Domyślny adres `http://localhost:8000`.
- W `packages/rae-mcp-server/mcp_config.json`:
  - Aktualizacja na `"RAE_API_URL": "http://localhost:8000"`.

### Krok 2: Automatyczna okresowa konsolidacja pamięci pasywnej (GAP-2)
- Dodanie licznika przechwyconych śladów `self._trace_counter` w `PassiveMemoryInterceptor`.
- Po osiągnięciu `auto_consolidate_interval` (domyślnie 20 wywołań narzędzi), interceptor asynchronicznie uruchamia w tle zadanie `consolidate_traces(project=project)`.
- Rezultat: pełna, bezobsługowa pętla samouczenia w RAE.

### Krok 3: Rozszerzenie API `EmbeddedRAE` o pełny CRUD (GAP-3)
- Dodanie metod:
  - `async def get(self, memory_id: UUID) -> Optional[Dict[str, Any]]`
  - `async def delete(self, memory_id: UUID) -> bool`
  - `async def list(self, layer: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]`
- Rozszerzenie `packages/rae-agentic-memory/rae-core/tests/unit/test_embedded_rae.py` o testy weryfikujące pełny cykl życia `store -> get -> list -> query -> delete`.

### Krok 4: Weryfikacja testów `rae-phoenix` i higiena podmodułów (GAP-4, GAP-5)
- Uruchomienie zestawu testów `rae-phoenix` i upewnienie się, że `test_enhanced_rae_client.py` i `test_phoenix_closed_loop.py` przechodzą w 100%.
- Zatwierdzenie zmian w podmodułach zgodnie z Submodule-First Git Flow.

### Krok 5: Całościowa weryfikacja końcowa i audyt
- Uruchomienie pełnego pakietu testów `rae-core`, `EmbeddedRAE`, `DeterministicReflection` i `rae-mcp-server`.
- Weryfikacja zerowej liczby ostrzeżeń lintera (`ruff check`).
- Rejestracja wykonania za pomocą `scripts/record_task_completion.py` z rozgłoszeniem na siatkę potrójnej replikacji (Laptop, Cloud, Node 1).
