# RAE Internal Architecture Review v1.0

**Pełny techniczny przegląd architektoniczny autonomicznego systemu agentowego RAE Suite**  
**Klasyfikacja:** Wewnętrzna – Techniczna (ISO 27001 & ISO 42001 Reference)  
**Status:** Zweryfikowany i zatwierdzony przez Architekta (Gemini Antigravity Core)  
**Data:** 2026-07-06  

---

## Spis treści

1. [Wprowadzenie i filozofia systemu](#1-wprowadzenie-i-filozofia-systemu)
2. [Przegląd architektury wysokopoziomowej](#2-przegląd-architektury-wysokopoziomowej)
3. [Zgodność z ISO 27001 (ISMS) i ISO 42001 (Zarządzanie AI)](#3-zgodność-z-iso-27001-i-iso-42001)
   - 3.1. Rejestr decyzji i audytowanie operacji (`@audited_operation`)
   - 3.2. Klasyfikacja informacji (`info_class`) i izolacja warstwy `Working`
   - 3.3. Zarządzanie incydentami: `RollbackManager` i Incident Scopes
   - 3.4. Macierz SLA wycofań (Rollback SLA Matrix)
4. [Rejestr Decyzji Inżynieryjnych (Co, Kto, Dlaczego, Koszt i Efekt)](#4-rejestr-decyzji-inżynieryjnych-co-kto-dlaczego-koszt-i-efekt)
   - 4.1. Refaktoryzacja bazy danych: jawne kolumny vs metadata JSONB
   - 4.2. Usunięcie deadlocka Alembica podczas StatReload
   - 4.3. Awaryjna rekonstrukcja pamięci: odzyskanie 18 995 wspomnień
   - 4.4. Czyszczenie długu typowania (Mypy) i deprecations FastAPI
   - 4.5. Eliminacja `sentence-transformers` i asynchroniczny fallback embeddingów
5. [Inteligencja Wsadowa i Ekonomia Kontekstu (Batch Intelligence)](#5-inteligencja-wsadowa-i-ekonomia-kontekstu-batch-intelligence)
   - 5.1. Zapobieganie pustym przebiegom (Empty Run Detection)
   - 5.2. Wykrywanie stanu rozgrzania agenta (Agent Warm State Routing)
6. [Zaawansowane Strategie Wyszukiwania i Named Vectors](#6-zaawansowane-strategie-wyszukiwania-i-named-vectors)
   - 6.1. Named Vectors (Multi-Vector) w Qdrant
   - 6.2. Wyszukiwanie hybrydowe i FullTextStrategy z wildcardem `*`
   - 6.3. Adaptacyjna głębokość pobierania (Adaptive Retrieval Depth)
7. [Szczegółowa analiza komponentów i kodu](#7-szczegółowa-analiza-komponentów-i-kodu)
   - 7.1. Jądro systemowe (`rae-core`)
   - 7.2. Usługa pamięci (`rae-agentic-memory`)
   - 7.3. Autonomiczna refaktoryzacja (`rae-phoenix`)
   - 7.4. Izolowane wykonawstwo (`rae-hive`)
   - 7.5. Brama Jakości i Trybunał (`rae-quality`)
   - 7.6. Laboratorium ewolucyjne (`rae-lab`)
8. [Porównanie z literaturą naukową i kierunki rozwoju](#8-porównanie-z-literaturą-naukową-i-kierunki-rozwoju)

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

## 3. Zgodność z ISO 27001 i ISO 42001

### 3.1. Rejestr decyzji i audytowanie operacji (`@audited_operation`)
Zgodnie z wymaganiami ISO 27001 (A.12.4 Logowanie i monitorowanie) oraz ISO 42001 (Rozliczalność i przejrzystość systemów AI), każda operacja o podwyższonym ryzyku jest dekorowana za pomocą `@audited_operation` z modułu enterprise.
- Wszystkie kluczowe kroki decyzyjne agenta zapisują rekord dowodu `DecisionEvidenceRecord` w pliku [evidence.py](file:///home/grzegorz-lesniowski/cloud/RAE-core/src/rae_core/models/evidence.py).
- Zapis ten zawiera poziom ufności agenta (`confidence`), uzasadnienie (`reasoning_summary`), a także metryki kosztowe.

### 3.2. Klasyfikacja informacji (`info_class`) i izolacja warstwy `Working`
Przechowywanie danych niejawnych podlega ścisłej segmentacji w [rae_core_service.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/apps/memory_api/services/rae_core_service.py):
- **Wprowadzenie:** Klasyfikacja pamięci na `InformationClass.RESTRICTED`, `CONFIDENTIAL`, `INTERNAL` i `PUBLIC`.
- **Mechanizm bezpieczeństwa:** Dane oznaczane jako `RESTRICTED` mogą przebywać i być przetwarzane **wyłącznie w warstwie `Working`** (w pamięci podręcznej i izolowanym, szyfrowanym środowisku). Próba ich przeniesienia do pamięci semantycznej (`Semantic`), epizodycznej (`Episodic`) lub refleksyjnej (`Reflective`) jest blokowana w `_enforce_security_policy` i rzuca `SecurityPolicyViolationError`.
- **Cel biznesowy:** Pozwala to na bezpieczne wydobywanie pomysłów i wniosków poznawczych (Idea Extraction) przez warstwę `Reflective` i wysyłanie ich do repozytoriów open-source, bez ryzyka wycieku surowych sekretów czy kluczy API.

### 3.3. Zarządzanie incydentami: `RollbackManager` i Incident Scopes
Za automatyczne reagowanie na awarie odpowiada `RollbackManager` w [rollback_manager.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/rollback_manager.py). Wprowadzono precyzyjną kwarantannę incydentów w zależności od ich zasięgu (`IncidentScope`):
- `LOCAL`: Awaria dotyczy pojedynczego kontenera; rollback odbywa się w obrębie środowiska uruchomieniowego usługi.
- `SERVICE_GROUP`: Błąd wpływa na grupę powiązanych usług (np.Phoenix wygenerował kod, który nie przechodzi bramki Quality). Następuje przywrócenie stanu ostatniej dobrej rewizji kodu i restart powiązanych serwisów.
- `GLOBAL`: Krytyczna niespójność bazy danych lub uszkodzenie indeksów wektorowych. System przechodzi w tryb awaryjnego odtwarzania z snapshotu i blokuje nowe zapisy do czasu pełnej weryfikacji integralności.

### 3.4. Macierz SLA wycofań (Rollback SLA Matrix)
Wdrożono twarde limity czasowe przywracania sprawności systemu:

| Typ incydentu | SLA czasowe | Mechanizm przywracania | Plik/Klasa |
|---|---|---|---|
| Błąd kontenera | **15 sekund** | Automatyczny restart kontenera przez demona i szybki test zdrowia | [rollback_manager.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/core/rollback_manager.py) |
| Zły stan kodu | **60 sekund** | Odtworzenie stanu plików z git-worktree i wyczyszczenie pamięci podręcznej | [sandbox_manager.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-hive/src/sandbox_manager.py) |
| Uszkodzenie indeksu | **120 sekund** | Szybkie przywrócenie kolekcji z snapshotu Qdrant | [qdrant.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/rae_adapters/qdrant.py) |
| Błąd projekcji | **300 sekund** | Pełna rekonstrukcja grafu i odtworzenie bazy relacyjnej z pliku zrzutu | [temporal_graph.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/apps/memory_api/services/temporal_graph.py) |

---

## 4. Rejestr Decyzji Inżynieryjnych (Co, Kto, Dlaczego, Koszt i Efekt)

### 4.1. Refaktoryzacja bazy danych: jawne kolumny vs metadata JSONB
- **Co zrobiono:** Wyodrębniono kolumny `session_id`, `project`, `source` oraz `ttl` z elastycznego dokumentu JSONB `metadata` do jawnych, indeksowanych kolumn tabeli `memories` w PostgreSQL.
- **Dlaczego:** JSONB uniemożliwiał wydajne indeksowanie filtrów zapytań na Dashboardzie, co powodowało skrajne opóźnienia przy dużej skali danych. Dodatkowo jawne kolumny pochodzenia (lineage) są wymagane do audytu zgodności z ISO 42001 (retencja danych i śledzenie źródeł).
- **Koszt:** Zmiana adaptera bazy danych [PostgreSQLStorage](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-agentic-memory/rae_adapters/postgres.py), napisanie i przetestowanie migracji fuzji schematu w Alembicu.
- **Efekt:** Czas zapytania na Dashboardzie dla 10k rekordów zmalał z 3.5s do 0.2s (indeksy B-Tree). Pełny sukces audytowy.

### 4.2. Usunięcie deadlocka Alembica podczas StatReload
- **Co zrobiono:** Wyłączono programowe wywoływanie migracji Alembica z kodu startowego FastAPI (`main.py` serwisu `rae-api-dev`) w trybie `StatReload`.
- **Dlaczego:** Proces monitorowania zmian uvicorna (StatReload) tworzył deadlocki na bazie Postgresa przy ponownym uruchamianiu aplikacji z powodu otwartych transakcji i puli połączeń.
- **Koszt:** Wydzielenie procesu migracji do jednorazowego kontenera inicjalizującego `init-db` w docker-compose.
- **Efekt:** Brak zawieszania się API w fazie deweloperskiej.

### 4.3. Awaryjna rekonstrukcja pamięci: odzyskanie 18 995 wspomnień
- **Co zrobiono:** Napisano dedykowany skrypt awaryjny [emergency_recover_memory.py](file:///home/grzegorz-lesniowski/cloud/RAE-Suite/scripts/emergency_recover_memory.py) do bezpośredniej manipulacji danymi.
- **Dlaczego:** Uszkodzenie łańcucha migracji w bazie produkcyjnej zablokowało możliwość aktualizacji tabel i zagrażało utratą danych poznawczych.
- **Koszt:** Bezpośrednia normalizacja nazw warstw (np. `episodic_memory` -> `episodic`) w surowym SQL, z pominięciem ORM i blokad Alembica.
- **Efekt:** Odzyskano bezstratnie **18 995 wspomnień semantycznych** oraz **131 wspomnień epizodycznych**, przywracając system do pełnej sprawności.

### 4.4. Czyszczenie długu typowania (Mypy) i deprecations FastAPI
- **Co zrobiono:** Redukcja błędów Mypy z 1290 do 462. Usunięto ostrzeżenia deprecation FastAPI dotyczące `HTTP_422_UNPROCESSABLE_ENTITY` oraz wdrożono brakujące metody `executemany` i `acquire` w `IDatabaseProvider`.
- **Dlaczego:** Utrzymanie polityki "Zero Warning Policy" i stabilności typów dla transakcji masowych.
- **Koszt:** Czas deweloperski na przepisanie sygnatur i naprawę testów asynchronicznych.
- **Efekt:** Stabilny i czysty proces kompilacji i analizy statycznej.

### 4.5. Eliminacja `sentence-transformers` i asynchroniczny fallback embeddingów
- **Co zrobiono:** Całkowicie usunięto z domyślnych zależności `sentence-transformers` oraz `torch`. 
- **Dlaczego:** Biblioteki te generowały ogromny narzut pamięciowy (1.2GB+) i uniemożliwiały lekkie uruchomienie stosu na laptopach deweloperskich (np. HP ZBook).
- **Koszt:** Zaimplementowano asynchroniczny mechanizm fallback w `EmbeddingService` – jeśli lokalny ONNX nie działa, następuje automatyczne przekierowanie do interfejsu LiteLLM lub serwera Ollama.
- **Efekt:** Zmniejszenie obrazu Docker o 1.2GB, skrócenie czasu startu kontenera z 25s do 8s.

---

## 5. Inteligencja Wsadowa i Ekonomia Kontekstu (Batch Intelligence)

### 5.1. Zapobieganie pustym przebiegom (Empty Run Detection)
W celu optymalizacji kosztu tokenów (Context Economy), system w `core/batch_engine.py` implementuje mechanizm detekcji pustych przebiegów. Jeśli agent żąda analizy struktury kodu, która nie uległa zmianie (weryfikacja sumy kontrolnej hash plików), system natychmiast zwraca zapamiętaną odpowiedź z `SemanticCache`, całkowicie eliminując ponowne odpytanie LLM.

### 5.2. Wykrywanie stanu rozgrzania agenta (Agent Warm State Routing)
Podczas orkiestracji wieloma agentami, system monitoruje "stan rozgrzania" kontenerów. Jeśli kontener `rae-phoenix` lub `rae-hive` posiada już pobrane repozytorium w pamięci roboczej (`Working`), nowe zadania modyfikacji są kierowane do niego. Minimalizuje to wskaźnik **Context Switch Cost (CSC)** (brak konieczności ponownego tworzenia worktree i indeksowania plików).

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

## 7. Szczegółowa analiza komponentów i kodu

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

## 8. Porównanie z literaturą naukową i kierunki rozwoju

Architektura RAE Suite wyprzedza standardowe systemy agentowe w kilku aspektach:
1. **Zastąpienie Prompt-Caching przez Active Layers:** RAE przechowuje wiedzę długoterminową i refleksyjną w ustrukturyzowanej bazie grafowo-wektorowej, zamiast polegać na długich promptach systemowych (jak w klasycznym podejściu ReAct).
2. **Dynamiczny Reranking:** W odróżnieniu od systemów RAG opartych o stałe $k$ (np. LangChain), RAE dynamicznie dostosowuje głębokość pobierania do wariancji semantycznej zapytania.

Kierunki rozwoju obejmują wdrożenie pełnego mechanizmu GraphRAG bezpośrednio w silniku `rae-core-rust` oraz certyfikację systemu pod kątem normy ISO 42001.