# RAE Full Configuration Map (Silicon Oracle v5.0)

**Kompleksowy rejestr zmiennych środowiskowych, plików konfiguracyjnych i domyślnych wartości na każdym poziomie suity RAE**  
**Klasyfikacja:** Techniczna / Dokumentacyjna  
**Status:** ZWERYFIKOWANY Z KODEM ŹRÓDŁOWYM  

Dokument ten inwentaryzuje wszystkie parametry konfiguracyjne każdego modułu wchodzącego w skład ekosystemu RAE. Umożliwia precyzyjne dostrajanie zachowania agentów, pamięci wektorowej, baz danych oraz polityk bezpieczeństwa.

---

## 1. Konfiguracja Orkiestratora i Jądra (RAE-Suite Core)

Jądro orkiestracji CEO jest sterowane przez zmienne środowiskowe oraz plik specyfikacji deklaratywnej.

### A. Zmienne środowiskowe (`rae_suite_orchestrator.py` & `.env`):
*   `RAE_API_URL` (Domyślnie: `http://rae-memory:8000` w Dockerze, `http://localhost:8011` lokalnie): Adres API pamięci poznawczej.
*   `ORCHESTRATION_TICK` (Domyślnie: `60` sekund): Częstotliwość wywoływania pętli orkiestracji (zbieranie sygnałów, sprawdzanie backlogu i uzgadnianie stanu).
*   `FACTORY_SPEC_PATH` (Domyślnie: `factory.yaml`): Ścieżka do pliku specyfikacji fabryki agentów.
*   `CEO_PLANNING_AGENT` (Domyślnie: `rae-oracle-gemini`): Główny agent planujący przydzielany do trybunału i analizy backlogu.
*   `RAE_PROFILE` (Domyślnie: `dev`): Profil uruchomieniowy (np. `dev`, `prod`, `laptop`).

### B. Plik specyfikacji fabryki (`factory.yaml`):
*   `factory_id` (Wartość: `node1-factory-v3`): Unikalny identyfikator instancji fabryki.
*   `active_departments` (Wartości: `planning`, `production`, `quality`, `lab`): Aktywne wydziały/moduły.
*   `costModel` (Koszt wykonania zadań):
    *   `baseUnit`: `NCU` (Neural Compute Units).
    *   `weights.input_tokens`: `0.000001` (Waga kosztu tokena wejściowego).
    *   `weights.output_tokens`: `0.000002` (Waga kosztu tokena wyjściowego).
    *   `weights.wall_time_s`: `0.01` (Koszt czasu wykonania w sekundach).

---

## 2. Konfiguracja Pamięci (rae-agentic-memory)

Najbardziej rozbudowany moduł konfiguracyjny (`apps/memory_api/config.py`). Wykorzystuje bibliotekę `pydantic-settings` do walidacji.

### A. Baza danych i Wektory:
*   `POSTGRES_HOST` (Domyślnie: `rae-am-postgres`): Host PostgreSQL (z rozszerzeniem pgvector).
*   `POSTGRES_DB` (Domyślnie: `rae`): Nazwa bazy danych.
*   `POSTGRES_USER` (Domyślnie: `rae`): Użytkownik bazy danych.
*   `POSTGRES_PASSWORD` (Domyślnie: `rae_password`): Hasło do bazy danych.
*   `QDRANT_HOST` (Domyślnie: `rae-am-qdrant`): Host silnika wektorowego Qdrant.
*   `QDRANT_PORT` (Domyślnie: `6333`): Port usługi Qdrant.
*   `CELERY_BROKER_URL` (Domyślnie: `redis://rae-am-redis:6379/1`): Kolejka zadań Celery.
*   `CELERY_RESULT_BACKEND` (Domyślnie: `redis://rae-am-redis:6379/2`): Miejsce zapisu wyników Celery.
*   `REDIS_URL` (Domyślnie: `redis://rae-am-redis:6379/0`): Baza danych Redis dla cache i rate-limitera.

### B. Silniki LLM i Embeddings:
*   `RAE_EMBEDDING_BACKEND` (Domyślnie: `onnx`): Backend generowania embeddingów (np. `onnx` dla lokalnych modeli ONNX bez wyjścia do sieci, `api` dla chmurowych).
*   `RAE_LLM_MODEL_DEFAULT` (Domyślnie: `ollama/qwen2.5:1.5b`): Domyślny model do syntezy.
*   `OLLAMA_API_URL` (Domyślnie: `http://ollama-dev:11434`): Adres serwera Ollama.
*   `RAE_LLM_BACKEND` (Domyślnie: `ollama`): Wybrany backend wnioskowania.
*   `EXTRACTION_MODEL` (Domyślnie: `gpt-4o-mini`): Model do ekstrakcji encji.
*   `SYNTHESIS_MODEL` (Domyślnie: `gpt-4o`): Model do zaawansowanej syntezy refleksyjnej.
*   `RAE_RERANKER_BACKEND` (Domyślnie: `emerald`): Wybrany model rerankera (np. `emerald` lub `math`).
*   `RAE_USE_GPU` (Domyślnie: `False`): Flaga włączająca akcelerację GPU CUDA dla modeli ONNX.

### C. Bezpieczeństwo i Wielodostępność (Tenancy & Security):
*   `TENANCY_ENABLED` (Domyślnie: `True`): Włączenie izolacji danych według klientów (Multi-Tenancy).
*   `DEFAULT_TENANT_UUID` (Domyślnie: `00000000-0000-0000-0000-000000000000`): Domyślny UUID dzierżawcy.
*   `ENABLE_API_KEY_AUTH` (Domyślnie: `False`): Włączenie autoryzacji tokenem API.
*   `ENABLE_JWT_AUTH` (Domyślnie: `False`): Włączenie autoryzacji tokenami JWT.
*   `ENABLE_RATE_LIMITING` (Domyślnie: `False`): Włączenie ograniczenia liczby zapytań API.
*   `RATE_LIMIT_REQUESTS` (Domyślnie: `100` / `RATE_LIMIT_WINDOW: 60`): Domyślny limit (100 zapytań na minutę).

### D. Wagi Poznawcze (Math V3 weights):
Parametry do wyliczania rankingu wspomnień przez `rae-core/math/policy.py`:
*   `MATH_V3_W1_RELEVANCE` (Wartość: `0.40`): Rezonans semantyczny (podobieństwo cosinusowe).
*   `MATH_V3_W2_IMPORTANCE` (Wartość: `0.20`): Istotność poznawcza nadana przez trybunał.
*   `MATH_V3_W3_RECENCY` (Wartość: `0.10`): Czasowy rozpad pamięci (świeżość).
*   `MATH_V3_W4_CENTRALITY` (Wartość: `0.10`): Zagęszczenie relacji w grafie pojęć.
*   `MATH_V3_W5_DIVERSITY` (Wartość: `0.10`): Współczynnik różnorodności (unikani duplikatów).
*   `MATH_V3_W6_DENSITY` (Wartość: `0.10`): Zagęszczenie informacyjne w sąsiedztwie semantycznym.

### E. Retencja, Rozpad i Konsolidacja (Decay & Summarization):
*   `MEMORY_RETENTION_DAYS` (Domyślnie: `30` dni): Czas przechowywania wspomnień sensorycznych.
*   `MEMORY_DECAY_RATE` (Domyślnie: `0.01`): Bazowy współczynnik zapominania wspomnień.
*   `MEMORY_IMPORTANCE_DECAY_ENABLED` (Domyślnie: `True`): Rozpad istotności w czasie.
*   `MEMORY_IMPORTANCE_DECAY_SCHEDULE` (Domyślnie: `"0 2 * * *"`): Harmonogram cron (codziennie o 02:00 w nocy).
*   `REFLECTIVE_MEMORY_ENABLED` (Domyślnie: `True`): Włączenie pętli refleksyjnej.
*   `REFLECTIVE_MEMORY_MODE` (Domyślnie: `full` / opcjonalnie `lite` dla słabych urządzeń).
*   `DREAMING_ENABLED` (Domyślnie: `False` / `full` tryb nadpisuje na `True`): Włączenie asynchronicznych procesów konsolidacji marzeń sennych agenta (wyciąganie wniosków w tle).
*   `DREAMING_MIN_IMPORTANCE` (Domyślnie: `0.6`): Minimalny próg istotności zdarzenia do konsolidacji.
*   `SUMMARIZATION_ENABLED` (Domyślnie: `True`): Agregacja powtarzalnych mikrowydarzeń.

---

## 3. Konfiguracja Planisty (RAE-Phoenix)

Konfiguracja architektoniczna i weryfikacyjna w pliku `packages/rae-phoenix/feniks/config/settings.py`.

### A. Ustawienia Bazowe:
*   `qdrant_collection` (Domyślnie: `feniks_kb_test`): Kolekcja wektorowa bazy wiedzy Phoenixa.
*   `embedding_model` (Domyślnie: `all-MiniLM-L6-v2`): Model transformacji kodu na wektory.
*   `rae_enabled` (Domyślnie: `False`): Flaga integracji z pamięcią RAE.
*   `rae_timeout` (Domyślnie: `30` sekund): Maksymalny czas oczekiwania na odpowiedź z jądra RAE.

### B. Polityki Ryzyka i Zabezpieczeń (Behavior Policy):
*   `behavior_max_risk_threshold` (Domyślnie: `0.5`): Maksymalny akceptowalny wskaźnik ryzyka dla operacji (0.0 - 1.0).
*   `behavior_critical_threshold` (Domyślnie: `0.7`): Próg krytyczny ryzyka (natychmiastowo kierowany do zatwierdzenia przez człowieka).
*   `behavior_zero_regression_enabled` (Domyślnie: `False`): Flaga bezwzględnej blokady regresji testów.
*   `behavior_min_coverage_scenarios` (Domyślnie: `5`): Wymagana liczba scenariuszy testowych przy generowaniu kontraktu behawioralnego.
*   `behavior_contract_min_snapshots` (Domyślnie: `3`): Minimalna liczba wykonanych zrzutów stanu do wygenerowania stabilnego wzorca zachowania.
*   `behavior_comparison_strict_mode` (Domyślnie: `False`): Tryb ścisłego porównywania plików i wyjść konsoli.

---

## 4. Konfiguracja Wykonawcy (RAE-Hive)

Konfiguracja współpracy agentów i uprawnień w `packages/rae-hive/config/hive_protocol.yaml`.

### A. Konfiguracja Ogólna:
*   `hive_id` (Wartość: `RAE-HIVE-ALPHA`): Identyfikator roju.
*   `memory.api_url` (Domyślnie: `http://localhost:8001`): URL bazy wiedzy roju.
*   `memory.project` (Domyślnie: `RAE-Hive`): Nazwa projektu dla logów telemetrycznych.

### B. Przypisanie Modelowe (Model Router):
*   `models.coder`: `deepseek-coder-v2:16b` (Model do pisania kodu).
*   `models.reasoner`: `qwen2.5:14b` (Model do planowania).
*   `models.fast_chat`: `llama3.1:8b` (Model do szybkich pogawędek/klasyfikacji).
*   `models.embedding`: `nomic-embed-text` (Model embeddingów).

### C. Role i Uprawnienia Agentów (Swarm Permissions):
*   **Orchestrator:**
    *   Model: `reasoner`
    *   Uprawnienia: `["read_all", "write_tasks", "delegate"]`
    *   Warstwa pamięci: `reflective`
*   **Builder:**
    *   Model: `coder`
    *   Uprawnienia: `["read_semantic", "write_episodic", "file_system_write"]`
    *   Warstwa pamięci: `working`
*   **Auditor:**
    *   Model: `reasoner`
    *   Uprawnienia: `["read_episodic", "write_reflective", "file_system_read"]`
    *   Warstwa pamięci: `episodic`

---

## 5. Konfiguracja Strażnika Jakości (RAE-Quality)

Zmienne środowiskowe i progi zdefiniowane bezpośrednio w `packages/rae-quality/main.py` oraz `engines/governance/tribunal.py`.

### A. Zmienne Środowiskowe:
*   `RAE_API_URL` (Domyślnie: `http://rae-memory:8000` lub `http://localhost:8000`): Endpoint API pamięci.
*   `TRIBUNAL_TIER2_AGENT` (Domyślnie: `rae-local-reasoner`): Model apelacyjny w sądzie 3-stopniowym.
*   `TRIBUNAL_TIER3_AGENT` (Domyślnie: `rae-oracle-gemini`): Model najwyższy (Sąd Najwyższy) analizujący ryzyko krytyczne.

### B. Bramki Jakościowe (Quality Gate Baselines):
*   `baseline_coverage` (Domyślnie: `80.0`%): Minimalne wymagane pokrycie testami jednostkowymi. Kod z mniejszym pokryciem jest automatycznie odrzucany.
*   `baseline_vulnerabilities` (Domyślnie: `0`): Maksymalna dozwolona liczba krytycznych podatności bezpieczeństwa.
*   Minimalny wynik Seniority (`SeniorityRanker`): `0.70`. Kod poniżej tej oceny (klasyfikowany jako `Junior Developer`) jest automatycznie odrzucany, co wymusza aktywną interwencję naprawczą Phoenixa.

---

## 6. Konfiguracja Laboratorium Ewolucyjnego (RAE-Lab)

Parametry optymalizacyjne zdefiniowane w `packages/rae-lab/metrics_aggregator.py`.

### A. Uczenie Ze Wzmocnieniem (MAB Tuner):
Modyfikacja wag decyzji routingowych w oparciu o algorytm Multi-Armed Bandit:
*   `alpha` (Wartość: `0.4`): Początkowa waga dla dokładności wykonania zadania.
*   `beta` (Wartość: `0.3`): Początkowa waga dla minimalizacji opóźnień.
*   `gamma` (Wartość: `0.3`): Początkowa waga dla oszczędności finansowych/tokenowych.
*   `Granice wag` (Wartość: `[0.05, 0.85]`): Reguła zapobiegania nieskończonym pętlom decyzyjnym (Anti-Looping rule). Żadna z wag nie może spaść poniżej 5% ani przekroczyć 85% w procesie samouczenia.
