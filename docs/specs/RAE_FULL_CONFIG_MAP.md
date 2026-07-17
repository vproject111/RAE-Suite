# RAE Full Configuration Map (Silicon Oracle v5.0)

**Kompleksowy rejestr zmiennych środowiskowych, plików konfiguracyjnych, strategii i domyślnych wartości na każdym poziomie suity RAE**  
**Klasyfikacja:** Techniczna / Dokumentacyjna  
**Status:** ZWERYFIKOWANY Z KODEM ŹRÓDŁOWYM  

Dokument ten inwentaryzuje wszystkie parametry konfiguracyjne, dynamiczne strategie wyszukiwania oraz polityki zatwierdzania jakości każdego modułu wchodzącego w skład ekosystemu RAE.

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

## 2. Konfiguracja Pamięci i Strategii Wyszukiwania (rae-agentic-memory)

Moduł pamięci poznawczej udostępnia zaawansowaną konfigurację bazodanową oraz wybór matematycznych i językowych strategii wyszukiwania.

### A. Tryby i Strategie Wyszukiwania Hybrydowego (`routes/hybrid_search.py`):
Wyszukiwanie hybrydowe pozwala na włączanie i wyłączanie poszczególnych silników wyszukiwania w zapytaniu:
*   `enable_vector_search` (Toggles: `True`/`False`): Wyszukiwanie podobieństwa wektorowego w chmurze punktów Qdrant.
*   `enable_semantic_search` (Toggles: `True`/`False`): Wyszukiwanie pojęciowe oparte o kluczowe węzły semantyczne.
*   `enable_graph_search` (Toggles: `True`/`False`): Wyszukiwanie powiązań relacyjnych poprzez graf wiedzy (z limitem głębokości `graph_max_depth`, domyślnie `3`).
*   `enable_fulltext_search` (Toggles: `True`/`False`): Klasyczne wyszukiwanie tekstowe z użyciem indeksu GIN i wildcardów (`*`).
*   `enable_reranking` (Toggles: `True`/`False`): Włączenie dodatkowego stopnia rerankingu wyników.

### B. Wagi i Strategie Manifold (Math logic_gateway.py):
Wybór aktywnego ramienia matematycznego fusion (Manifold Arm) w jądrze poznawczym:
*   `system_1_ib` (System 1 - Implicit Behavior): Szybkie, heurystyczne łączenie na podstawie powtarzalnych wzorców zachowań.
*   `system_37_hyper`: Hiperwymiarowa synteza wektorowa przeznaczona do złożonych korelacji faktów.
*   `system_41_scalpel`: Precyzyjne, lingwistyczne cięcie kontekstu (słowa kluczowe i metadane).
*   `system_100_fluid`: Płynne łączenie uwzględniające silny rozpad czasowy i dynamiczną ważność wspomnień.
*   `legacy_416`: Klasyczna strategia hybrydowa RAE v2.6.
*   `silicon_oracle` (Wybór domyślny): Produkcyjna, wielowarstwowa synteza poznawcza (najwyższa precyzja).

### C. Zmienne Środowiskowe Pamięci (`apps/memory_api/config.py`):
*   `RAE_REFLECTION_STRATEGY` (Wartość: `hybrid` lub `math`): `math` generuje refleksje czysto deterministyczne, `hybrid` wspiera generowanie "Lessons Learned" przez model LLM.
*   `RAE_RERANKER_MODE` (Wartość: `math` lub `llm`): `math` używa algorytmu re-rankingu wagi poznawczej, `llm` używa modelu językowego.
*   `POSTGRES_HOST`, `QDRANT_HOST`, `REDIS_URL`: Konfiguracja połączeń usług.
*   `RAE_EMBEDDING_BACKEND` (Wartość: `onnx`): Zapewnia lokalne, bezwyjściowe generowanie embeddingów.
*   `RAE_LLM_MODEL_DEFAULT` (Wartość: `ollama/qwen2.5:1.5b`): Model do syntezy.

### D. Wagi Poznawcze (Math V3 weights):
*   `MATH_V3_W1_RELEVANCE` (`0.40`): Podobieństwo wektorowe.
*   `MATH_V3_W2_IMPORTANCE` (`0.20`): Istotność nadana przez trybunał.
*   `MATH_V3_W3_RECENCY` (`0.10`): Świeżość (czas od zapisu).
*   `MATH_V3_W4_CENTRALITY` (`0.10`): Powiązanie w grafie.
*   `MATH_V3_W5_DIVERSITY` (`0.10`): Eliminacja duplikatów semantycznych.
*   `MATH_V3_W6_DENSITY` (`0.10`): Zagęszczenie informacyjne.

---

## 3. Konfiguracja Planisty i Walidacji Jakości (RAE-Phoenix)

Moduł Phoenix konfiguruje reguły refaktoryzacji oraz zatwierdzania proponowanych zmian.

### A. Strategie i Polityki Zatwierdzania Jakości (`feniks/core/policies/`):
*   **ZeroRegressionPolicy (`behavior_zero_regression_enabled`):**
    *   Wymusza twardy warunek: nowo wygenerowany kod nie może spowodować żadnej regresji w istniejących testach jednostkowych ani integracyjnych.
*   **MaxBehaviorRiskPolicy (`behavior_max_risk_threshold`, domyślnie `0.5`):**
    *   Wylicza stopień ryzyka zmiany (`risk_score`). Jeżeli ryzyko przekroczy próg (np. `0.5` dla standardowych zmian, `0.7` próg krytyczny), propozycja jest natychmiast blokowana.
*   **MinimumCoverageBehaviorPolicy:**
    *   Wymusza minimalną liczbę scenariuszy testowych (`behavior_min_coverage_scenarios` domyślnie `5`) i asercji w kodzie testowym (`behavior_min_coverage_checks` domyślnie `3`).
*   **QualityPolicyEnforcer (`core/policies/quality_policy.py`):**
    *   `min_thought_length` (Domyślnie `10` znaków): Odrzuca kroki wnioskowania agenta, jeśli jego proces myślowy ("thought") był zbyt krótki (wykrywanie powierzchownego planowania).
    *   `forbidden_patterns` (Domyślnie: `["I don't know what to do", "just guessing"]`): Odrzuca i renegocjuje plany, jeśli model wyraża w nich niepewność lub brak determinizmu.

### B. Kontrakt Zatwierdzania Poprawek (Phoenix-Quality Bridge):
*   `PHOENIX_LLM_AGENT` (Domyślnie: `rae-oracle-gemini`): Model główny wykonujący refaktoryzację.
*   **Warunek Akceptacji (Hard Contract):** Kod po refaktoryzacji jest akceptowany wyłącznie wtedy, gdy wynik audytu Quality Sentinel zwróci status `PASSED` **oraz** stopień zaawansowania kodu (`seniority_attained`) zostanie sklasyfikowany jako `advanced_senior` (wynik wyliczenia `SeniorityRanker` $\ge 0.90$). W innym wypadku Phoenix automatycznie podejmuje kolejną próbę (maks. `5` prób) lub wywołuje `FAILED_ESCALATED` z pełnym wycofaniem (rollback).

---

## 4. Konfiguracja Wykonawcy (RAE-Hive)

Konfiguracja współpracy agentów i uprawnień w `packages/rae-hive/config/hive_protocol.yaml`.

*   `models.coder`: `deepseek-coder-v2:16b` (Pisanie kodu).
*   `models.reasoner`: `qwen2.5:14b` (Rozumowanie i krytyka).
*   **Uprawnienia ról (Permissions Matrix):**
    *   `orchestrator` (Rola planująca): `["read_all", "write_tasks", "delegate"]`.
    *   `builder` (Rola programistyczna): `["read_semantic", "write_episodic", "file_system_write"]`.
    *   `auditor` (Rola weryfikująca): `["read_episodic", "write_reflective", "file_system_read"]`.

---

## 5. Konfiguracja Strażnika Jakości (RAE-Quality)

Parametry audytu kodu i testów w `packages/rae-quality/main.py`.

*   `baseline_coverage` (Domyślnie: `80.0`%): Minimalny akceptowalny próg pokrycia kodu testami.
*   `baseline_vulnerabilities` (Domyślnie: `0`): Dopuszczalna liczba krytycznych błędów bezpieczeństwa (SAST/Trivy).
*   `TestIntegrityGuard`: Wykrywa próby oszukiwania testów przez model (np. usuwanie asercji, mockowanie na poziomie krytycznym).

---

## 6. Konfiguracja Laboratorium Ewolucyjnego (RAE-Lab)

Parametry optymalizacyjne zdefiniowane w `packages/rae-lab/metrics_aggregator.py`.

*   **Wagi Multi-Armed Bandit (MAB Tuner):**
    *   `alpha` (Waga dokładności: `0.4`).
    *   `beta` (Waga opóźnienia: `0.3`).
    *   `gamma` (Waga kosztu tokenów: `0.3`).
    *   `Granice optymalizacji`: `[0.05, 0.85]` (Zabezpieczenie przed dominacją jednej metryki i pętleniem wyboru modeli).
