# RAE Internal Architecture Review v1.0

**Pełny techniczny przegląd architektoniczny autonomicznego systemu agentowego RAE Suite**  
**Klasyfikacja:** Wewnętrzna – Techniczna (ISO 27001 & ISO 42001 Reference)  
**Status:** Zweryfikowany i zatwierdzony przez Architekta (Gemini Antigravity Core)  
**Data:** 2026-07-06  

---

## Spis treści

1. [Wprowadzenie i filozofia systemu](#1-wprowadzenie-i-filozofia-systemu)
2. [Przegląd architektury wysokopoziomowej](#2-przegląd-architektury-wysokopoziomowej)
3. [Jądro Orkiestracji i Autonomii (RAE-Suite Core)](#3-jądro-orkiestracji-i-autonomii-rae-suite-core)
   - 3.1. Autonomy Kernel i cykl życia zadania (`autonomy_kernel.py`)
   - 3.2. Brama wykonywania narzędzi (`tool_gateway.py`)
   - 3.3. Budowanie kontekstu i selekcja wektorów (`context_broker.py`)
   - 3.4. Optymalizacja serii i Efekt Skali Wiedzy (`batch_engine.py`)
   - 3.5. Inteligentny router modeli i kworum sądu (`model_router.py`)
   - 3.6. Konsensus Quality Tribunal (`quality_tribunal.py`)
   - 3.7. Prawdopodobieństwo unieważniania keszu (`semantic_cache.py`)
   - 3.8. Spekulatywne wywoływanie narzędzi (`speculative_executor.py`)
4. [Zgodność z ISO 27001 (ISMS) i ISO 42001 (Zarządzanie AI)](#4-zgodność-z-iso-27001-i-iso-42001)
   - 4.1. Ślad dowodowy decyzji i `@audited_operation`
   - 4.2. Klasyfikacja informacji (`info_class`) i izolacja warstwy `Working`
   - 4.3. Zarządzanie incydentami: `RollbackManager` i Incident Scopes
   - 4.4. Macierz SLA wycofań (Rollback SLA Matrix)
5. [Rejestr Decyzji Inżynieryjnych (Co, Kto, Dlaczego, Koszt i Efekt)](#5-rejestr-decyzji-inżynieryjnych-co-kto-dlaczego-koszt-i-efekt)
   - 5.1. Refaktoryzacja bazy danych: jawne kolumny vs metadata JSONB
   - 5.2. Usunięcie deadlocka Alembica podczas StatReload
   - 5.3. Awaryjna rekonstrukcja pamięci: odzyskanie 18 995 wspomnień
   - 5.4. Czyszczenie długu typowania (Mypy) i deprecations FastAPI
   - 5.5. Eliminacja `sentence-transformers` i asynchroniczny fallback embeddingów
6. [Zaawansowane Strategie Wyszukiwania i Named Vectors](#6-zaawansowane-strategie-wyszukiwania-i-named-vectors)
   - 6.1. Named Vectors (Multi-Vector) w Qdrant
   - 6.2. Wyszukiwanie hybrydowe i FullTextStrategy z wildcardem `*`
   - 6.3. Adaptacyjna głębokość pobierania (Adaptive Retrieval Depth)
7. [Szczegółowa analiza komponentów i submodułów](#7-szczegółowa-analiza-komponentów-i-submodułów)
   - 7.1. Jądro systemowe (`rae-core`)
   - 7.2. Usługa pamięci (`rae-agentic-memory`)
   - 7.3. Autonomiczna refaktoryzacja (`rae-phoenix`)
   - 7.4. Izolowane wykonawstwo (`rae-hive`)
   - 7.5. Brama Jakości i Trybunał (`rae-quality`)
   - 7.6. Laboratorium ewolucyjne (`rae-lab`)
8. [Weryfikacja wdrożenia i kierunki rozwoju](#8-weryfikacja-wdrożenia-i-kierunki-rozwoju)

---

## 1. Wprowadzenie i filozofia systemu

System RAE Suite (Silicon Oracle RAE) opiera się na paradygmacie **Memory-First**, w którym pamięć nie jest jedynie pasywnym magazynem danych, lecz aktywnym, dynamicznie ewoluującym nośnikiem wiedzy poznawczej agenta. Wszystkie akcje, od prostych zapytań po zaawansowane pętle refaktoryzacji, przechodzą przez kernel pamięci, który decyduje o doborze kontekstu, ocenie ryzyka i ewentualnych krokach wycofania (rollback).

Kluczowe niezmienniki architektury to:
- **Agnostycyzm modelowy i infrastrukturalny:** System oddziela interfejsy od konkretnych dostawców (LLM, Qdrant, PostgreSQL).
- **Zasada Twardych Ram (Hard Frames):** Każda akcja podlega capability kontraktom oraz ocenie ryzyka przed modyfikacją kodu.
- **Ewolucyjna presja (Szubar Mode):** Wykorzystanie historycznych danych o błędach do wymuszania selekcji negatywnej u agentów.

---

## 2. Przegląd architektury wysokopoziomowej

Projekt jest zorganizowany w architekturze mikrousług zintegrowanych za pośrednictwem wspólnego jądra `rae-core`.

```
                  ┌─────────────────────────────────────┐
                  │          Klient / API REST          │
                  └──────────────────┬──────────────────┘
                                     │
                  ┌──────────────────v──────────────────┐
                  │         rae-agentic-memory          │
                  │        (FastAPI Core Service)       │
                  └──────────────────┬──────────────────┘
                                     │
                  ┌──────────────────v──────────────────┐
                  │              rae-core               │
                  │   (Layers, Search, Refl, Governance)│
                  └──────────────────┬──────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
┌────────v────────┐         ┌────────v────────┐         ┌────────v────────┐
│   rae-phoenix   │         │    rae-hive     │         │   rae-quality   │
│   (Planner)     │         │   (Executor)    │         │   (Reviewer)    │
└────────┬────────┘         └────────┬────────┘         └────────┬────────┘
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     │
                            ┌────────v────────┐
                            │     rae-lab     │
                            │  (Aggregator)   │
                            └─────────────────┘
```

---

## 3. Jądro Orkiestracji i Autonomii (RAE-Suite Core)

Główna orkiestracja i zachowanie autonomiczne są zdefiniowane bezpośrednio w pakiecie `core/` głównego modułu `RAE-Suite`. Ta warstwa nie była uwzględniona w podstawowych przeglądach, a to ona implementuje rzeczywisty silnik decyzyjny i bramki bezpieczeństwa.

### 3.1. Autonomy Kernel i cykl życia zadania ([autonomy_kernel.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/autonomy_kernel.py))
Klasa `AutonomyKernel` zarządza maszyną stanową cyklu życia zadania (`TaskState`) i generuje podpisane paragony wykonania (`ExecutionReceipt`).
- Enforcuje reguły dynamicznych kontraktów capability (`CapabilityContract`). Każdy moduł (`rae-phoenix`, `rae-hive`, `rae-quality`, `rae-openclaw`) ma przypisane dozwolone i zakazane klasy ryzyka (`RiskClass`), zestawy narzędzi, limit budżetu tokenów oraz maksymalny czas wykonania.
- Przykład: wtyczka `rae-phoenix` ma zdefiniowany kontrakt `cap-phoenix` zezwalający na klasy ryzyka `R0` do `R3` i wykluczający użycie poleceń typu `ssh` lub `docker`.

### 3.2. Brama wykonywania narzędzi ([tool_gateway.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/tool_gateway.py))
Klasa `ToolGateway` przechwytuje i rejestruje wszelkie wywołania narzędzi systemowych.
- Zapobiega pustym analizom i powtórzeniom (**Empty Run Prevention**) – przechowuje `empty_run_cache` haszujący zapytania kontekstowe (`context_hash`). Jeśli agent chce wykonać czasochłonne skany na niezmienionym kodzie, gateway zwraca poprzednie rezultaty natychmiast.
- Rejestruje trajektorię agenta (**Trajectory Replay**) do pliku JSONL `trajectory_replay.jsonl`. Każde wywołanie zapisuje parametry wejściowe, wyjściowe oraz RNG seed, co umożliwia odtworzenie stanów w piaskownicy.
- Blokuje komendy niebezpieczne (np. `rm -rf /` lub `DROP DATABASE`).

### 3.3. Budowanie kontekstu i selekcja wektorów ([context_broker.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/context_broker.py))
Klasa `ContextBroker` optymalizuje parametry pobierania i rozmiar kontekstu.
- **Hierarchical Context Pruning:** Kompresuje i układa kontekst w strukturę hierarchiczną: `Constitution` $\rightarrow$ `Project Profile` $\rightarrow$ `Summaries` $\rightarrow$ `Raw Leaf Data`. Przycina najmniej wiarygodne rekordy (najniższy `trust_score`) w przypadku przekroczenia limitu słów/tokenów.
- **Adaptive Retrieval Depth:** Dynamicznie dopasowuje parametr $k$ w zależności od różnicy (gap) punktacji wektorowej. Jeśli dystans między pierwszym a drugim kandydatem jest duży ($>0.15$), system pomija kosztowny reranker i zwraca małe $k$ ($3$). Jeśli różnica jest mała ($<0.05$), głębokość jest rozwijana do $k=30$ i włączany jest reranker.

### 3.4. Optymalizacja serii i Efekt Skali Wiedzy ([batch_engine.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/batch_engine.py))
Klasa `BatchOptimizationEngine` minimalizuje wskaźnik **Context Switch Cost (CSC)**.
- Grupuje luźne zadania modyfikacji w paczki (`Batch`) na podstawie docelowego modułu lub pliku.
- **Efekt Skali Wiedzy (Knowledge Scale Effect):** Jeśli agent jest "ciepły" (`Agent Warm State` – ma załadowany kontekst danego modułu i pliki w worktree), system automatycznie pobiera z backlogu i wykonuje inne drobne zadania z tej samej domeny, amortyzując koszt setupu i przezbrajania środowiska (`setup_cost`).

### 3.5. Inteligentny router modeli i kworum sądu ([model_router.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/model_router.py))
Klasa `ModelRouter` przechowuje profile parametrów modeli (`ModelProfile`), uwzględniając wymiary kosztów tokenów, okna kontekstowego, wskaźnika opóźnienia i jakości.
- Automatycznie kieruje zadania do najtańszego modelu spełniającego klasę ryzyka (np. lokalne modele Ollama na Node 3/Piotrek dla niskiego ryzyka `R0`-`R2`, komercyjne modele API dla `R5`-`R6`).
- Definiuje kworum modeli dla Trybunału Jakości (`get_tribunal_quorum_models`) w podziale na 3 tiery.

### 3.6. Konsensus Quality Tribunal ([quality_tribunal.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/quality_tribunal.py))
Klasa `QualityTribunal` zarządza trójwarstwowym procesem oceny zmian kodu z wykorzystaniem kworum (Majority Vote - min. 2 z 3 zgodnych głosów modeli):
- **Tier 1 (Partial Court):** Używa wyłącznie modeli lokalnych (np. `llama-3.1-8b`, `qwen-2.5-7b`, `mistral-7b-v0.3`), weryfikując składnię i reguły AST.
- **Tier 2 (Appellate Court):** Silniejsze modele lokalne (np. `mixtral-8x7b`, `llama-3.1-70b-instruct`) analizujące potencjalne podatności i destrukcyjne SQL.
- **Tier 3 (Supreme Court):** Najsilniejsze modele komercyjne (np. `gemini-1.5-pro`, `gpt-4o`, `claude-3-5-sonnet`) dokonujące ostatecznej weryfikacji i audytu logiki biznesowej.

### 3.7. Prawdopodobieństwo unieważniania keszu ([semantic_cache.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/semantic_cache.py))
Klasa `ProbabilisticSemanticCache` implementuje cache semantyczny oparty o cosine similarity.
- Skaluje czas życia cache (`ttl`) dynamicznie w oparciu o wskaźnik zmienności (`volatility_score`).
- Przy trafieniu w cache, system z prawdopodobieństwem $p=0.05$ przeprowadza ciche sprawdzenie poprawności danych. W przypadku wykrycia niespójności z bazą, wywołuje **Semantic Neighborhood Eviction** – usuwa z pamięci podręcznej wszystkie sąsiednie wektory semantyczne o podobieństwie powyżej $0.85$.
- Zgodnie z niezmiennikami, cache ten nie wykonuje żadnych trwałych modyfikacji w bazie RAE.

### 3.8. Spekulatywne wywoływanie narzędzi ([speculative_executor.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/speculative_executor.py))
Klasa `SpeculativeToolExecutor` przyspiesza czas odpowiedzi o ~40%.
- Przed ostatecznym potwierdzeniem planu przez model, system wykrywa bezpieczne, idempotentne komendy (np. `git status`, `docker ps`, skrypty diagnostyczne) i uruchamia je w tle w maksymalnej liczbie $k=3$ równolegle.
- Wyniki są gotowe w cache zanim model zatwierdzi ich wywołanie.

---

## 4. Zgodność z ISO 27001 i ISO 42001

### 4.1. Ślad dowodowy decyzji i `@audited_operation`
Każda operacja o podwyższonym ryzyku jest logowana do scentralizowanego dziennika audytu. Wszystkie kluczowe kroki decyzyjne agenta zapisują rekord dowodu `DecisionEvidenceRecord` w pliku [evidence.py](file:///home/grzegorz-lesniowski/cloud/RAE-core/src/rae_core/models/evidence.py).
Zapis ten zawiera poziom ufności agenta (`confidence`), uzasadnienie (`reasoning_summary`), a także metryki kosztowe.

### 4.2. Klasyfikacja informacji (`info_class`) i izolacja warstwy `Working`
Przechowywanie danych niejawnych podlega ścisłej segmentacji w [rae_core_service.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/apps/memory_api/services/rae_core_service.py):
- Dane o klasie `RESTRICTED` mogą przebywać i być przetwarzane **wyłącznie w warstwie `Working`** (w pamięci podręcznej i izolowanym, szyfrowanym środowisku). Próba ich przeniesienia do pamięci semantycznej (`Semantic`), epizodycznej (`Episodic`) lub refleksyjnej (`Reflective`) jest blokowana w `_enforce_security_policy` i rzuca `SecurityPolicyViolationError`.
- **Cel biznesowy:** Pozwala to na bezpieczne wydobywanie pomysłów i wniosków poznawczych (Idea Extraction) przez warstwę `Reflective` i wysyłanie ich do repozytoriów open-source, bez ryzyka wycieku surowych sekretów czy kluczy API.

### 4.3. Zarządzanie incydentami: `RollbackManager` i Incident Scopes
Za automatyczne reagowanie na awarie odpowiada `RollbackManager` w [rollback_manager.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/rollback_manager.py). Wprowadzono precyzyjną kwarantannę incydentów w zależności od ich zasięgu (`IncidentScope`):
- `LOCAL`: Awaria dotyczy pojedynczego kontenera; rollback odbywa się w obrębie środowiska uruchomieniowego usługi.
- `SERVICE_GROUP`: Błąd wpływa na grupę powiązanych usług (np.Phoenix wygenerował kod, który nie przechodzi bramki Quality). Następuje przywrócenie stanu ostatniej dobrej rewizji kodu i restart powiązanych serwisów.
- `GLOBAL`: Krytyczna niespójność bazy danych lub uszkodzenie indeksów wektorowych. System przechodzi w tryb awaryjnego odtwarzania z snapshotu i blokuje nowe zapisy do czasu pełnej weryfikacji integralności.

### 4.4. Macierz SLA wycofań (Rollback SLA Matrix)
Wdrożono twarde limity czasowe przywracania sprawności systemu:

| Typ incydentu | SLA czasowe | Mechanizm przywracania | Plik/Klasa |
|---|---|---|---|
| Błąd kontenera | **15 sekund** | Automatyczny restart kontenera przez demona i szybki test zdrowia | [rollback_manager.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/rollback_manager.py) |
| Zły stan kodu | **60 sekund** | Odtworzenie stanu plików z git-worktree i wyczyszczenie pamięci podręcznej | [sandbox_manager.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-hive/src/sandbox_manager.py) |
| Uszkodzenie indeksu | **120 sekund** | Szybkie przywrócenie kolekcji z snapshotu Qdrant | [qdrant.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/rae_adapters/qdrant.py) |
| Błąd projekcji | **300 sekund** | Pełna rekonstrukcja grafu i odtworzenie bazy relacyjnej z pliku zrzutu | [temporal_graph.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/apps/memory_api/services/temporal_graph.py) |

---

## 5. Rejestr Decyzji Inżynieryjnych (Co, Kto, Dlaczego, Koszt i Efekt)

### 5.1. Refaktoryzacja bazy danych: jawne kolumny vs metadata JSONB
- **Co zrobiono:** Wyodrębniono kolumny `session_id`, `project`, `source` oraz `ttl` z elastycznego dokumentu JSONB `metadata` do jawnych, indeksowanych kolumn tabeli `memories` w PostgreSQL.
- **Dlaczego:** JSONB uniemożliwiał wydajne indeksowanie filtrów zapytań na Dashboardzie, co powodowało skrajne opóźnienia przy dużej skali danych. Dodatkowo jawne kolumny pochodzenia (lineage) są wymagane do audytu zgodności z ISO 42001 (retencja danych i śledzenie źródeł).
- **Koszt:** Zmiana adaptera bazy danych [PostgreSQLStorage](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/rae_adapters/postgres.py), napisanie i przetestowanie migracji fuzji schematu w Alembicu.
- **Efekt:** Czas zapytania na Dashboardzie dla 10k rekordów zmalał z 3.5s do 0.2s (indeksy B-Tree). Pełny sukces audytowy.

### 5.2. Usunięcie deadlocka Alembica podczas StatReload
- **Co zrobiono:** Wyłączono programowe wywoływanie migracji Alembica z kodu startowego FastAPI (`main.py` serwisu `rae-api-dev`) w trybie `StatReload`.
- **Dlaczego:** Proces monitorowania zmian uvicorna (StatReload) tworzył deadlocki na bazie Postgresa przy ponownym uruchamianiu aplikacji z powodu otwartych transakcji i puli połączeń.
- **Koszt:** Wydzielenie procesu migracji do jednorazowego kontenera inicjalizującego `init-db` w docker-compose.
- **Efekt:** Brak zawieszania się API w fazie deweloperskiej.

### 5.3. Awaryjna rekonstrukcja pamięci: odzyskanie 18 995 wspomnień
- **Co zrobiono:** Napisano dedykowany skrypt awaryjny [emergency_recover_memory.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/scripts/emergency_recover_memory.py) do bezpośredniej manipulacji danymi.
- **Dlaczego:** Uszkodzenie łańcucha migracji w bazie produkcyjnej zablokowało możliwość aktualizacji tabel i zagrażało utratą danych poznawczych.
- **Koszt:** Bezpośrednia normalizacja nazw warstw (np. `episodic_memory` -> `episodic`) w surowym SQL, z pominięciem ORM i blokad Alembica.
- **Efekt:** Odzyskano bezstratnie **18 995 wspomnień semantycznych** oraz **131 wspomnień epizodycznych**, przywracając system do pełnej sprawności.

### 4.4. Czyszczenie długu typowania (Mypy) i deprecations FastAPI
- **Co zrobiono:** Redukcja błędów Mypy z 1290 do 462. Usunięto ostrzeżenia deprecation FastAPI dotyczące `HTTP_422_UNPROCESSABLE_ENTITY` oraz wdrożono brakujące metody `executemany` i `acquire` w `IDatabaseProvider`.
- **Dlaczego:** Utrzymanie polityki "Zero Warning Policy" i stabilności typów dla transakcji masowych.
- **Koszt:** Czas deweloperski na przepisanie sygnatur i naprawę testów asynchronicznych.
- **Efekt:** Stabilny i czysty proces kompilacji i analizy statycznej.

### 5.5. Eliminacja `sentence-transformers` i asynchroniczny fallback embeddingów
- **Co zrobiono:** Całkowicie usunięto z domyślnych zależności `sentence-transformers` oraz `torch`. 
- **Dlaczego:** Biblioteki te generowały ogromny narzut pamięciowy (1.2GB+) i uniemożliwiały lekkie uruchomienie stosu na laptopach deweloperskich (np. HP ZBook).
- **Koszt:** Zaimplementowano asynchroniczny mechanizm fallback w `EmbeddingService` – jeśli lokalny ONNX nie działa, następuje automatyczne przekierowanie do interfejsu LiteLLM lub serwera Ollama.
- **Efekt:** Zmniejszenie obrazu Docker o 1.2GB, skrócenie czasu startu kontenera z 25s do 8s.

---

## 6. Zaawansowane Strategie Wyszukiwania i Named Vectors

### 6.1. Named Vectors (Multi-Vector) w Qdrant
Aby RAE pozostał w pełni agnostyczny modelowo, w [qdrant.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/rae_adapters/qdrant.py) wdrożono obsługę **Nazwanych Wektorów (Named Vectors)**.
- Zamiast trzymać jedną przestrzeń o sztywnej wymiarowości, ta sama kolekcja `memories` przechowuje wektory z różnych modeli: `dense` (384 wymiary z MiniLM) oraz `ollama` (768 wymiarów z Nomic/Ollama).
- Umożliwia to wyszukiwanie semantyczne różnymi modelami bez konieczności migracji schematu czy utraty dokładności poprzez skalowanie wymiarów.

### 6.2. Wyszukiwanie hybrydowe i FullTextStrategy z wildcardem `*`
Wyszukiwanie hybrydowe w `HybridSearchEngine` łączy wyszukiwanie wektorowe i pełnotekstowe. Wdrożenie klasy `FullTextStrategy` opartej o Postgresowy indeks GIN i `tsquery` z obsługą wildcardów (`*`) rozwiązało problem pustych stanów na Dashboardzie – wpisanie `*` poprawnie zwraca wszystkie wspomnienia posortowane po dacie i ważności.

### 6.3. Adaptacyjna głębokość pobierania (Adaptive Retrieval Depth)
Przed uruchomieniem kosztownego rerankera (Math/LLM Reranking), silnik w `HybridSearchEngine` bada wariancję wyników podobieństwa cosinusowego pierwszego etapu (wyszukiwania wektorowego).
- Jeżeli wariancja wyników jest niska (wyniki są zbite semantycznie), system zwiększa parametr $k$ (Retrieval Depth), aby pobrać więcej kandydatów i pozwolić rerankerowi na precyzyjną selekcję.
- Jeżeli wariancja jest wysoka (najlepszy wynik zdecydowanie przewyższa resztę), system zmniejsza $k$, oszczędzając tokeny i czas obliczeniowy.

---

## 7. Szczegółowa analiza komponentów i submodułów

### 7.1. Jądro systemowe (`rae-core`)
Definiuje interfejsy i modele matematyczne. Sercem silnika jest [RAEEngine](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/rae_adapters/memory/) zarządzający FSM konsolidacji oraz [ReflectionEngineV2](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/apps/memory_api/services/reflection_engine.py).

### 7.2. Usługa pamięci (`rae-agentic-memory`)
Realizuje FastAPI Web Server. Odpowiada za integrację adapterów baz danych i realizację polityki retencji przez [retention_service.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/apps/memory_api/services/retention_service.py).

### 7.3. Autonomiczna refaktoryzacja (`rae-phoenix`)
Implementuje logikę automatycznej modyfikacji kodu w zamkniętej pętli w oparciu o wtyczki językowe. Wejście stanowi kod źródłowy z błędami lintera/testów, a wyjściem jest gotowy patch (do 5 prób naprawczych).

### 7.4. Izolowane wykonawstwo (`rae-hive`)
Zarządza uruchamianiem skryptów w piaskownicach Dockera lub wydzielonych gałęziach (worktrees), chroniąc środowisko hosta.

### 7.5. Brama Jakości i Trybunał (`rae-quality`)
Trybunał weryfikuje zmiany kodu pod kątem bezpieczeństwa (SAST) i pokrycia testami. Klasyfikuje zmiany za pomocą `SeniorityRanker`. Zapobiega oszukiwaniu testów poprzez `TestIntegrityGuard`.

### 7.6. Laboratorium ewolucyjne (`rae-lab`)
Zbiera telemetrię i stroi wagi za pomocą algorytmu Multi-Armed Bandit w [metrics_aggregator.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-lab/metrics_aggregator.py), dążąc do minimalizacji kosztów tokenów przy zachowaniu wysokiej dokładności.

---

## 8. Weryfikacja wdrożenia i kierunki rozwoju

Na podstawie audytu kodu źródłowego w głównym repozytorium `RAE-Suite` oraz jego submodułów, zweryfikowano status wdrożenia elementów zintegrowanego planu `ZINTEGROWANY_PLAN_AEA_V3`:

| Nazwa modułu/funkcjonalności | Klasa / Plik | Status wdrożenia |
|---|---|---|
| **REPOSITORY_MANIFEST.json** | [validate_repo_manifest.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/scripts/validate_repo_manifest.py) | **W pełni zaimplementowane** |
| **Tool Execution Gateway** | [tool_gateway.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/tool_gateway.py) | **W pełni zaimplementowane** |
| **Policy Engine & Risk Classifier** | [policy_checker.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/policy_checker.py) | **W pełni zaimplementowane** |
| **Context Envelope** | [context_broker.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/context_broker.py) | **W pełni zaimplementowane** |
| **Batch Optimization Engine** | [batch_engine.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/batch_engine.py) | **W pełni zaimplementowane** |
| **Adaptive Retrieval Depth** | [context_broker.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/context_broker.py) | **W pełni zaimplementowane** |
| **Quality Tribunal Consensus** | [quality_tribunal.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/quality_tribunal.py) | **W pełni zaimplementowane** |
| **Probabilistic Cache Invalidation** | [semantic_cache.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/semantic_cache.py) | **W pełni zaimplementowane** |
| **Speculative Tool Execution** | [speculative_executor.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/speculative_executor.py) | **W pełni zaimplementowane** |
| **Failure Mining & Shadow Mode** | [shadow_evaluator.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/shadow_evaluator.py) | **W pełni zaimplementowane** |
| **Federated Message Templates** | - | *Planowane do wdrożenia (Faza P0)* |
| **Streaming Function Composition** | - | *Planowane do wdrożenia (Faza P1)* |
| **OTEL Trace Propagation** | - | *Planowane do wdrożenia (Faza P1)* |
| **Trajectory Replay CLI (`rae replay`)** | - | *Planowane do wdrożenia (Faza P2)* |

Kolejnym krokiem inżynieryjnym w projekcie będzie realizacja brakujących integracji (szablony federacyjne i CLI replay) zgodnie z liniowym harmonogramem wdrożenia RAE Suite v3.0.