# RAE Full Capabilities Inventory (Silicon Oracle v5.0)

**Kompleksowy rejestr możliwości poznawczych, wykonawczych, zabezpieczeń oraz telemetrii suity RAE**  
**Klasyfikacja:** Techniczna / Dokumentacyjna  
**Status:** ZWERYFIKOWANY Z KODEM ŹRÓDŁOWYM  

Dokument zawiera kompletną inwentaryzację możliwości technicznych każdego modułu ekosystemu RAE. Stanowi on podstawę do projektowania kart, wykresów i widoków w ujednoliconym interfejsie graficznym (UI).

---

## 1. Jądro Systemu i Orkiestracja (RAE-Suite Core)

Jądro orkiestracji zarządza cyklem życia zadań, weryfikacją polityk bezpieczeństwa oraz optymalizacją przepływów.

*   **Maszyna Stanów Autonomii (`AutonomyKernel`):**
    *   Śledzenie stanów zadania (`TaskState`): `RECEIVED` $\rightarrow$ `CLASSIFIED` $\rightarrow$ `POLICY_CHECKED` $\rightarrow$ `CAPABILITY_CHECKED` $\rightarrow$ `PLANNED` $\rightarrow$ `DRY_RUN` $\rightarrow$ `SANDBOX_EXECUTING` $\rightarrow$ `VERIFYING` $\rightarrow$ `QUALITY_GATE` $\rightarrow$ `COMPLETED` / `FAILED_ESCALATED`.
    *   Enforcement kontraktów możliwości (`CapabilityContract`): sprawdzanie dozwolonych narzędzi, limitów czasu i budżetów tokenów na agenta.
*   **Bramka Wykonawcza Narzędzi (`ToolGateway`):**
    *   Zapobieganie Pustym Przebiegom (`empty_run_cache`): detekcja identycznych analiz i zwracanie wyników z pamięci podręcznej.
    *   Rejestracja Trajektorii (`TrajectoryReplay`): logowanie zdarzeń wejścia/wyjścia (z seedami RNG) do formatu JSONL w celu debugowania.
*   **Zarządca Kontekstu (`ContextBroker`):**
    *   Hierarchical Context Pruning: dynamiczne przycinanie drzewa kontekstu na podstawie globalnego budżetu tokenów i współczynnika wiarygodności (`trust_score`).
    *   Adaptive Retrieval Depth: automatyczne dopasowywanie parametru $k$ (głębokości wyszukiwania) i aktywacja rerankera na podstawie wariancji punktacji wektorowej.
*   **Silnik Optymalizacji Serii (`BatchOptimizationEngine`):**
    *   Grupowanie zadań (Batching) według modułów/plików w celu zminimalizowania kosztu przezbrojenia środowiska (`setup_cost`).
    *   Wykrywanie stanu rozgrzania agenta (Agent Warm State) w celu optymalnego routowania.
*   **Propagacja Śladów (`TraceContextPropagator`):**
    *   Wstrzykiwanie i ekstrakcja standardowych nagłówków W3C `traceparent` w komunikacji HTTP i subprocesach.
*   **Rejestr Szablonów (`FederatedPromptRegistry`):**
    *   Kompilacja i wersjonowanie hierarchicznych szablonów promptów (`Base` $\rightarrow$ `Org` $\rightarrow$ `Team` $\rightarrow$ `Feature`) zabezpieczone sumami skrótu SHA-256.

---

## 2. Pamięć Poznawcza (RAE-agentic-memory)

Warstwa zarządzania wiedzą, pamięcią warstwową oraz relacjami pojęciowymi.

*   **Pamięć Warstwowa (Multi-layer Memory):**
    *   *Sensory:* Surowy strumień wejściowy (logi, OCR, pliki).
    *   *Working:* Krótkoterminowa pamięć robocza (aktywne zadanie).
    *   *Episodic:* Zdarzenia uszeregowane chronologicznie.
    *   *Semantic:* Zanonimizowane, ustrukturyzowane pojęcia i fakty.
    *   *Long-term:* Trwała baza wiedzy.
    *   *Reflective:* Wnioski i syntezy wyciągnięte z niższych warstw.
*   **Wyszukiwanie Hybrydowe (`HybridSearchEngine`):**
    *   Named Vectors: wielomodelowa przestrzeń wektorowa w Qdrant (np. 384d dense dla lekkich wyszukiwań, 768d dla Ollama).
    *   FullTextStrategy: pełnotekstowe wyszukiwanie słów kluczowych oparte o indeks GIN w PostgreSQL z obsługą wildcardów (`*`).
*   **Zarządzanie Bezpieczeństwem (`RAECoreService`):**
    *   Izolacja danych RESTRICTED: blokada przenoszenia danych poufnych poza warstwę `Working`.
*   **Silnik Konsolidacji i Refleksji (`ReflectionEngineV2`):**
    *   Okresowa synteza zdarzeń epizodycznych do wiedzy semantycznej i generowanie refleksji z użyciem modeli LLM.
*   **Graf Wiedzy (`TemporalGraph`):**
    *   Zarządzanie relacjami między węzłami pojęć.
    *   Wykonywanie i przywracanie migawek grafu (`restore_snapshot`).
*   **Retencja i Cykl Życia Pamięci (`RetentionService`):**
    *   Matematyczny rozpad ważności (decay) wspomnień na podstawie czasu i częstotliwości odpytywania.

---

## 3. Planista i Architekt (RAE-Phoenix)

Silnik planowania refaktoryzacji, weryfikacji behawioralnej i naprawy kodu.

*   **Planista Poznawczy (`CognitivePlanner`):**
    *   MCTS/ToT (Monte Carlo Tree Search / Tree of Thoughts): generowanie 3 alternatywnych hipotez naprawy z wyliczeniem prawdopodobieństwa sukcesu (Win Probability).
*   **Weryfikacja Behawioralna (`RefactorEngine`):**
    *   Generowanie migawek zachowania (`BehaviorSnapshot`) przed i po modyfikacji kodu.
    *   Walidacja interakcji użytkownika (`UIAction`), API (`APIRequest`) oraz konsoli (`CLICommand`) za pomocą dedykowanych interpreterów (`PythonRunner`, `UIRunner`).
*   **Porównywanie Kontraktów (`ContractEngine`):**
    *   Ewaluacja regresji behawioralnej przy użyciu `BehaviorComparisonEngine` z blokadą zmian przy wskaźniku ryzyka `risk_score > 0.7`.
*   **Autonomiczna Pętla Naprawcza (Self-Repair Loop):**
    *   Cykliczne (maks. 3 próby) poprawianie kodu na podstawie negatywnych werdyktów z Quality Sentinel.

---

## 4. Wykonawca Środowiskowy (RAE-Hive)

Izolacja uruchomieniowa, delegacja obliczeń i audyty wizualne.

*   **Zarządzanie Piaskownicami (`SandboxManager`):**
    *   Automatyczna alokacja izolowanych katalogów roboczych (`git worktree`) i kontenerów Docker chroniących hosta.
*   **Spekulatywne Wykonawstwo (`SpeculativeToolExecutor`):**
    *   Równoległe, wyprzedzające uruchamianie maksymalnie 3 bezpiecznych narzędzi tylko do odczytu.
*   **Delegacja Obliczeń (Compute Offloading):**
    *   Obsługa pasywnego SSH do zdalnych węzłów obliczeniowych (Lumina, Julia) z automatycznym lokalnym fallbackiem.
*   **Audyt Wizualny (Visual Auditing):**
    *   Weryfikacja zmian w interfejsie użytkownika za pomocą testów Playwright i generowanie raportów wideo/obrazowych.

---

## 5. Strażnik Jakości (RAE-Quality)

Bramki wejściowe, SAST, konsensus sądu oraz ocena seniority.

*   **Bramka Jakości AST & Zero Warning Policy:**
    *   Weryfikacja składni (AST parser), wykrywanie tagów deweloperskich (`TODO`/`FIXME`) i brakujących importów.
*   **Trójwarstwowy Sąd Jakości (`QualityTribunal`):**
    *   *Tier 1 (Partial Court):* Szybkie lokalne modele weryfikujące poprawność techniczną.
    *   *Tier 2 (Appellate Court):* Średnie modele lokalne analizujące bezpieczeństwo SQL i wycieki.
    *   *Tier 3 (Supreme Court):* Zaawansowane modele komercyjne (Gemini/Claude) audytujące logikę biznesową.
*   **Analiza Statyczna i Testy:**
    *   Wyliczanie pokrycia testami (Coverage) i blokowanie regresji.
    *   Skanowanie podatności kontenera (Trivy) oraz sekretów w diffach (Gitleaks).
*   **Strażnik Testów (`TestIntegrityGuard`):**
    *   Analiza kodu testowego zapobiegająca celowemu osłabianiu asercji przez modele AI.
*   **Klasyfikator Kodu (`SeniorityRanker`):**
    *   Wykładnicze ocenianie jakości kodu i przypisywanie poziomu od `Junior Developer` do `Advanced Senior`.

---

## 6. Optymalizacja i Kaizen (RAE-Lab)

Strojenie systemu, zbieranie telemetrii oraz Shadow Mode.

*   **Strojenie Parametrów (Auto-Tuner):**
    *   Wykorzystanie algorytmu Multi-Armed Bandit (MAB) do optymalizacji wag modeli w zależności od dokładności i zużytych tokenów.
*   **Metryki Ekonomii Kontekstu:**
    *   Wyliczanie: Context Switch Cost (CSC), Batch Gain (zysk z serii), Amortization Rate (stopień zamortyzowania setupu), Batch Score.
*   **Tryb Cienia i Shadow Evaluation:**
    *   Shadow Rule Testing: weryfikacja nowych reguł w tle na historycznych trajektoriach.
    *   Shadow Model Evaluation: uruchamianie modeli kandydujących na kopiach ruchu bez wpływu na użytkownika.
*   **Wyszukiwanie Awarii (Failure Mining):**
    *   Analiza błędów z logów systemowych i automatyczna synteza nowych reguł obronnych (`Candidate Guardrails`).
