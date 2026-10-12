# 🛡️ PLAN NAPRAWY I OSIĄGNIĘCIA PERFEKCJI INŻYNIERYJNEJ RAE-SUITE V4.0
## Całościowy Audyt Architektury, Eliminacja Wąskich Gardeł i Pełne Zamknięcie Spójności Testów

**Data audytu:** 10 października 2026 r.  
**Lokalizacja:** `/home/grzegorz/cloud/RAE-Suite/docs/PLAN_NAPRAWY_PERFEKCJI_SUITE_V4.md`  
**Przedmiot audytu:** `core/`, `packages/rae-core`, `packages/rae-mcp-server`, `packages/rae-quality`, `packages/rae-hive`, `packages/rae-lab`, `tests/`  
**Standardy:** ISO 27001, ISO 42001, Zero Regression, Zero Drift, Hard Contract DTO Integrity.

---

## 1. WYNIKI GŁĘBOKIEGO AUDYTU (IDENTYFIKACJA LUK I NIEZGODNOŚCI)

Dogłębna analiza całego ekosystemu RAE-Suite ujawniła 8 precyzyjnych obszarów wymagających harmonizacji i naprawy:

| ID | Komponent / Moduł | Stan Wykryty | Konsekwencja / Ryzyko | Działanie Naprawcze |
|:---|:---|:---|:---|:---|
| **GAP-1** | `packages/rae-core/rae_core/models/improvement.py` & `mesh.py` | Brak klasy `Experiment` w modelach improvement oraz brak `ConsentGrant` i pełnej definicji `MeshExchangeEnvelope` w modelach mesh. | `ImportError` podczas ładowania modułów `core/test_improvement_plane.py` i `core/test_mesh.py`. | Uzupełnienie brakujących modeli DTO (`Experiment`, `ConsentGrant`, rozszerzenie `MeshExchangeEnvelope` i `ExperimentRun`). |
| **GAP-2** | `core/semantic_cache.py` | Zastąpienie `ProbabilisticSemanticCache` przez `HardenedSemanticCache` bez zachowania wstecznej zgodności. | `ImportError` w `core/test_phase2_integration.py` i `core/test_semantic_cache.py`. | Przywrócenie koegzystencji obu klas w module `core/semantic_cache.py`. |
| **GAP-3** | `core/quality_tribunal.py` | Metoda `evaluate_code_change` jest synchroniczna, podczas gdy część testów (`test_phase2_integration.py`, `test_quality_tribunal.py`) wywołuje ją z operatorem `await`. | `TypeError: object TribunalVerdict can't be used in 'await' expression`. | Implementacja protokołu `__await__` w `TribunalVerdict`, umożliwiająca użycie zarówno synchroniczne, jak i asynchroniczne. |
| **GAP-4** | `core/swarm_consensus.py` & `core/test_context_broker.py` | Niezgodność z rygorystycznymi kontraktami Pydantic (`extra="forbid"`): `proposal_id` zamiast `id` w `ConsensusProposal` oraz `context_id` w `ContextEnvelope`. | `ValidationError` przy tworzeniu obiektów kontraktowych. | Ujednolicenie pól kontraktowych (`id`, `source_hash`, Enumy `InformationClass` i `MemoryLayer`). |
| **GAP-5** | `core/model_router.py` | Brak wpisów dla modeli bazowych (`llama-3.1-8b`, `mixtral-8x7b`, `gemini-1.5-pro`) w domyślnym rejestrze oraz brak zgodności tekstowej typu `RouteDecision`. | `AssertionError` i `KeyError` w `test_model_router.py` i `test_phase1_integration.py`. | Dodanie brakujących profili do rejestru oraz implementacja `__eq__` i `__str__` w `RouteDecision`. |
| **GAP-6** | `core/test_rae_cli.py` & `core/test_integrity_guard.py` | Hardcodowana ścieżka `.venv/bin/python3` w teście CLI oraz ostrzeżenia Pytest o konstruktorze w klasie `TestIntegrityGuard`. | Błąd `FileNotFoundError` w środowiskach z inną ścieżką venv oraz `PytestCollectionWarning`. | Użycie `sys.executable` oraz oznaczenie klasy `__test__ = False`. |
| **GAP-7** | `pytest.ini` (Root RAE-Suite) | Brak pliku konfiguracyjnego `pytest.ini` w katalogu głównym RAE-Suite. | Pytest próbuje rekurencyjnie przetwarzać katalogi submodułów o innych środowiskach wykonawczych, generując błędy kolekcji. | Utworzenie pliku `pytest.ini` definiującego `testpaths` oraz `norecursedirs`. |
| **GAP-8** | `packages/rae-agentic-memory/rae_adapters/git_adapter.py` | Parametr `search_parent_directories=False` w `GitRuntimeAdapter`. | `InvalidGitRepositoryError`, gdy testy uruchamiane są z podkatalogu repozytorium. | Ustawienie `search_parent_directories=True` (już przetestowane i zweryfikowane). |

---

## 2. ETAPY REALIZACJI PLANU

### Etap 1: Uzupełnienie Modeli Kontraktowych (GAP-1)
- W `packages/rae-core/rae_core/models/improvement.py`:
  - Dodanie klasy `Experiment(experiment_id, name, hypothesis_id, candidate, success_criteria)`.
  - Rozszerzenie `ExperimentRun` o opcjonalne pola `experiment_id`, `metrics`, `trace_id`.
- W `packages/rae-core/rae_core/models/mesh.py`:
  - Dodanie klasy `ConsentGrant(grant_id, peer_id, scope, ttl_days, created_at)`.
  - Rozszerzenie pól w `MeshExchangeEnvelope` (`source_instance`, `target_peer_id`, `pack_id`, `consent_ref`, `expires_at`, `sensitivity_label`, `payload_data`, `provenance`).

### Etap 2: Koegzystencja Cache Semantycznego (GAP-2)
- W `core/semantic_cache.py`:
  - Zapewnienie dostępności zarówno `HardenedSemanticCache` (dla nowych etapów), jak i `ProbabilisticSemanticCache` (dla integracji fazy 2 i ewaluacji sąsiedztwa semantycznego).

### Etap 3: Uniwersalność Fasady Trybunału Jakości (GAP-3)
- W `core/quality_tribunal.py`:
  - Dodanie metody `__await__(self)` do klasy `TribunalVerdict`.

### Etap 4: Ścisłe Dostosowanie do Kontraktów RAE (GAP-4)
- W `core/swarm_consensus.py`:
  - Zmiana `proposal_id=proposal_id` na `id=proposal_id` w `ConsensusProposal`.
- W `core/test_context_broker.py`:
  - Aktualizacja parametrów testu `test_hierarchical_context_pruning` na zgodne ze schematem `ContextEnvelope`.

### Etap 5: Rejestr Modeli i Odporność Routera (GAP-5)
- W `core/model_router.py`:
  - Dodanie profili `llama-3.1-8b`, `mixtral-8x7b`, `gemini-1.5-pro`.
  - Wzbogacenie `RouteDecision` o `__eq__` (obsługa stringów) i `__str__`.
  - Dostosowanie `get_tribunal_quorum_models` do precyzyjnych reguł tierów.

### Etap 6: Porządki w Narzędziach i Testach (GAP-6, GAP-7)
- W `core/test_integrity_guard.py`: dodanie `__test__ = False`.
- W `test_factory_impulse.py`: dodanie `__test__ = False`.
- W `core/test_rae_cli.py`: zamiana `.venv/bin/python3` na `sys.executable`.
- Utworzenie `pytest.ini` w katalogu głównym RAE-Suite.

### Etap 7: Pełna Weryfikacja Testowa i Złożenie Zmian
- Uruchomienie `pytest` w katalogu głównym RAE-Suite.
- Uruchomienie `pytest` w `packages/rae-phoenix`, `packages/rae-mcp-server`, `packages/rae-quality`, `packages/rae-lab`, `packages/rae-hive`, `packages/rae-core`.
- Złożenie commitów z zachowaniem bramek Pre-Commit Gatekeeper.
- Rejestracja pomyślnego wykonania w pamięci RAE i rozgłoszenie po siatce Mesh.
