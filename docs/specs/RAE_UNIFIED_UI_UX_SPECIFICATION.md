# RAE Unified UI/UX Specification (Silicon Oracle v5.0)

**Specyfikacja ujednolicenia interfejsu użytkownika i doświadczenia poznawczego dla ekosystemu RAE**  
**Klasyfikacja:** Techniczna / Architektoniczna  
**Status:** ZATWIERDZONY DO REALIZACJI (AEA Program P3)  
**Autor:** Antigravity UI Architect  

---

## 1. Wizja Architektoniczna i Ograniczenia (Lightweight & Agnostic)

Głównym celem systemu RAE (Reflective Agentic Engine) jest zachowanie maksymalnej wydajności i możliwość uruchomienia rdzenia poznawczego (`rae-core`) na dowolnym urządzeniu: od potężnych klastrów obliczeniowych (RTX 4080 / i9), przez słabe laptopy deweloperskie (np. zintegrowana grafika, Windows), aż po urządzenia mobilne (Android/iOS).

Aby zrealizować ten cel bez narzucania ciężkich zależności (takich jak NodeJS/Next.js) na słabe urządzenia, architektura UI/UX zostaje podzielona na dwa tryby pracy (Hybrid Execution Mode):

```
                   ┌──────────────────────────────────┐
                   │    RAE Unified Client (Browser)  │
                   └────────────────┬─────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         │                                                     │
         ▼ (Tryb Standard: Docker / Server)                    ▼ (Tryb Lite: Mobilny / Offline)
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│     NiceGUI Quantum Portal      │                 │    Static PWA (Vue/Quasar CDN)  │
│  (Port 8080 - Server Side State)│                 │  (Single-File / Local Caching)  │
└────────────────┬────────────────┘                 └────────────────┬────────────────┘
                 │                                                   │
                 ▼                                                   ▼
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│        RAE-Suite API (8009)     │                 │       RAE-Lite API (SQLite)     │
└─────────────────────────────────┘                 └─────────────────────────────────┘
```

### Tryby Wykonania:
1.  **Tryb Standardowy (Connected Cluster):**
    *   Wizualizacja pełnej suity (Phoenix, Hive, Quality, Lab, Memory) za pośrednictwem serwera **NiceGUI** (`rae-portal` port `8080`).
    *   Wszystkie obliczenia i stany są utrzymywane po stronie serwera w Pythonie, a przeglądarka działa jako ultralekki klient renderujący Quasar/Vue.
2.  **Tryb Lekki (Offline-First / RAE-Lite):**
    *   Aplikacja typu **PWA (Progressive Web App)** załadowana do pamięci przeglądarki, która łączy się bezpośrednio z lokalnym silnikiem FastAPI/SQLite (uruchomionym lokalnie na Windowsie lub mobilnie wewnątrz WebView).
    *   Zero narzutu sieciowego, minimalne zużycie pamięci RAM.

---

## 2. Strategia Odporności na Cache (Cache-Resistance Strategy)

Jednym z największych problemów nowoczesnych aplikacji webowych dystrybuowanych lokalnie są konflikty pamięci podręcznej przeglądarki (stare wersje skryptów JS próbujące komunikować się z nowym API). Wdrożono cztery poziomy obrony przed problemami z cache:

### A. Nagłówki HTTP Cache-Control (API & Static Entrypoints)
Serwery FastAPI w RAE-Suite oraz serwer NiceGUI wymuszają bezwzględny brak buforowania plików konfiguracyjnych i punktu wejścia `index.html`:
```http
Cache-Control: no-cache, no-store, must-revalidate
Pragma: no-cache
Expires: 0
```

### B. Haszowanie Nazw Plików (Asset Hashing)
W procesie budowania obrazów produkcyjnych (Docker i kompilator `build_distribution.py`), wszystkie statyczne zasoby (JS, CSS) otrzymują unikalne nazwy oparte o hasz zawartości (np. `vendor.[contenthash].js`). 

### C. PWA Service Worker (Cache-First z Tłem Sieciowym)
Dla trybu offline PWA rejestruje Service Workera, który:
1.  Przechowuje statyczne pliki (ikony, czcionki Quasar) w `CacheStorage`.
2.  Przy każdym uruchomieniu wykonuje asynchroniczne zapytanie w tle (*background fetch*) w celu sprawdzenia wersji `manifest.json`.
3.  W razie wykrycia nowszej wersji kodu, wyświetla użytkownikowi nieblokujący baner: `"Dostępna jest nowa wersja RAE. [Odśwież teraz]"`, i automatycznie czyści stare rejestry cache przy przeładowaniu (`self.skipWaiting()`).

### D. Hydratacja Stanu z IndexedDB
Wszelkie formularze, trajektorie agentów i ustawienia są zapisywane w przeglądarce w bazie `IndexedDB` za pomocą biblioteki `localForage`. W przypadku nagłego odświeżenia strony (np. wymuszonego przez aktualizację cache), stan UI jest natychmiast odtwarzany (Hydrated) bez utraty wpisanych danych czy przerwanej sesji analizy.

---

## 3. System UI/UX i RWD (Responsive Design System)

Ujednolicony interfejs opiera się na bibliotece komponentów **Quasar (Vue3)** oraz klasach pomocniczych **TailwindCSS**, gwarantując spójność wizualną na monitorach 4K oraz ekranach smartfonów:

### Układ Adaptacyjny (Fluid Layout):
*   **Desktop:** Trójkolumnowy układ: nawigacja (lewa szuflada), główny panel roboczy (środek), panel refleksji i logów (prawa szuflada).
*   **Tablet/Mobile:** Szuflady są domyślnie schowane i wysuwane za pomocą gestów (*swipe*) lub menu hamburgera. Elementy wykresów eCharts automatycznie skalują swoją szerokość do rodzica (`resize()`).
*   **Aestetyka:** Ciemne motywy (Slate/Zinc-900), szklane rozmycia tła (`backdrop-filter`) dla okien dialogowych, precyzyjne mikroruchy dla wskaźników postępu agentów.

---

## 4. Architektura Integracji Modułów (Unified Dashboard View)

Ujednolicony interfejs webowy integruje wszystkie 5 modułów suity RAE w jednym spójnym widoku kontrolnym (Unified Dashboard View):

```
┌────────────────────────────────────────────────────────────────────────┐
│ [Hub Icon] RAE SUITE CONTROL PANEL                     [Brain Selection]│
├────────────────────────────────────────────────────────────────────────┤
│ 📃 Backlog   │          🔍 MONITOR PRACY AGENTÓW (GANTT)               │
│ Task-411 [ ] │                                                         │
│ Task-412 [✓] │ 🤖 Phoenix ─────────────────[Analiza kodu]              │
│ Task-413 [ ] │ 🤖 Hive    ────────────────────────────[Uruchomienie]   │
│              │ 🤖 Quality ─────────────────[Audyt 3-tier]              │
├──────────────┴─────────────────────────────────────────────────────────┤
│ 🧠 STAN PAMIĘCI POZNAWCZEJ                                            │
│ [Sensory: 12]  [Working: 4]  [Semantic: 18,995]  [Reflective: 131]     │
└────────────────────────────────────────────────────────────────────────┘
```

### A. Elementy Integracyjne Ogólne:
1.  **Monitor Pracy Agentów (Gantt Live-view):** Pokazuje, który moduł aktualnie wykonuje zadanie w piaskownicy w czasie rzeczywistym (Phoenix analizuje, Hive odpala testy, Quality przeprowadza sąd 3-warstwowy).
2.  **Cognitive Space Explorer:** Interaktywna wizualizacja grafu pamięci semantycznej z możliwością przeszukiwania i ręcznej edycji wspomnień.
3.  **Audit & Decision Ledger View:** Tabela pokazująca podpisane dowody decyzji (SLA wycofań, `@audited_operation` oraz statusy poprawek).

### B. Szczegółowa Integracja Pamięci (RAE-agentic-memory):
Interfejs webowy oferuje bezpośrednie instrumenty kontroli nad bazami poznawczymi:
1.  **Konsola Wyszukiwania Hybrydowego (Dynamic Search Console):**
    *   *Opis:* Panel sterowania pozwalający operatorowi ręcznie włączać/wyłączać silniki wyszukiwania (`enable_vector_search`, `enable_semantic_search`, `enable_graph_search`, `enable_fulltext_search`) w celach porównawczych.
    *   *Porównanie Strategii (Strategy Comparison):* Wyświetlanie wyników zapytania obok siebie w podziale na aktywną strategię matematyczną (np. `system_37_hyper` vs `system_41_scalpel`) wraz z metrykami trafności i czasem odpowiedzi w ms.
    *   *Suwaki Wag (Manual Weight Configurator):* Ręczne strojenie wag poznawczych (Relevance, Importance, Recency, Centrality, Diversity, Density) z natychmiastowym podglądem re-rankingu.
2.  **Krzywa Rozpadu Pamięci (Decay Curve & Retention Graph):**
    *   *Opis:* Wykres liniowy (eCharts) obrazujący spadek istotności (`importance_decay`) i siły wspomnień w czasie.
    *   *Zarządzanie retencją:* Tabela wspomnień z możliwością ręcznego zablokowania rozpadu (Protection Pin) zgodnie z parametrem `MEMORY_IMPORTANCE_PROTECTED_THRESHOLD_DAYS`.
3.  **Konsola Konsolidacji (Reflection & Dreaming Control):**
    *   *Opis:* Wskaźnik stanu asynchronicznego procesu konsolidacji marzeń sennych (`DREAMING_ENABLED`).
    *   *Wycinki refleksji:* Ręczne wyzwalanie syntezy epizodycznej do semantycznej oraz podgląd wygenerowanych przez LLM "Lessons Learned".
4.  **Panel Klasyfikacji i Dzierżawy (Multi-Tenancy & Data Classification):**
    *   *Opis:* Przełącznik aktywnego kontekstu klienta (`X-Tenant-Id`) oraz wizualne flagowanie poufności zasobów (`RESTRICTED` / `INTERNAL`).

### C. Szczegółowa Integracja Laboratorium (RAE-Lab):
Interfejs umożliwia wizualne monitorowanie i sterowanie ewolucją zachowania systemowego:
1.  **Monitor Uczenia Bandit (MAB Tuner Dashboard):**
    *   *Opis:* Dynamiczny wykres kołowy i liniowy pokazujący aktualne wagi decyzji modelu (`alpha` dokładność, `beta` opóźnienie, `gamma` koszt) strojne przez algorytm Multi-Armed Bandit.
    *   *Granice bezpieczeństwa:* Wizualizacja twardych barier `[0.05, 0.85]` uniemożliwiających dominację jednej metryki.
2.  **Statystyki Ekonomii Kontekstu (Context Economy Metrics):**
    *   *Opis:* Zestaw kart KPI prezentujący:
        *   **Context Switch Cost (CSC):** Koszt czasowy i tokenowy przełączania zadań.
        *   **Batch Gain:** Rzeczywisty czas i tokeny zaoszczędzone dzięki grupowaniu zadań przez `BatchOptimizationEngine` (wizualizacja zysków z serii).
        *   **Amortization Rate:** Stosunek kosztu setupu środowiska do liczby wykonanych operacji w sandboxie.
3.  **Tryb Cienia i Ewaluacja Modeli (Shadow Mode & Model Evaluator):**
    *   *Opis:* Panel porównujący na żywo dokładność modelu produkcyjnego z modelami testowymi uruchomionymi w tle (`Shadow Model Evaluation`).
    *   *Failure Mining:* Sekcja wyświetlająca wykryte anomalie z logów i wygenerowane reguły obronne (`Candidate Guardrails`) oczekujące na zatwierdzenie.

---

## 5. Dystrybucja i Uruchamianie na Słabych Urządzeniach

### 💻 A. Windows (Słaby Laptop deweloperski)
*   **Mechanizm:** RAE-Lite uruchamia się jako proces w tle. Ikona w tray'u systemowym pozwala na otwarcie przeglądarki pod adresem `http://localhost:8080`.
*   **Optymalizacja:** SQLite zastępuje PostgreSQL, a lokalne wektory w Qdrant-Lite działają w trybie jednowątkowym (brak narzutu na konteneryzację).

### 📱 B. Mobile (Smartfon / Android & iOS)
*   **Mechanizm:** PWA może być zainstalowane bezpośrednio na ekranie głównym telefonu.
*   **Zgodność:** Cały interfejs NiceGUI/Quasar jest zoptymalizowany pod kątem ekranów dotykowych (Touch targets min. 48x48px).

---

## 6. Harmonogram Realizacji (Roadmap)

### Iteracja 1: Przepisanie Portalu do Quasar/NiceGUI (Obecna faza)
*   Integracja kodu z `rae-portal` i przeniesienie go do ujednoliconego szablonu NiceGUI.
*   Wdrożenie adaptacyjnego layoutu dla urządzeń mobilnych.

### Iteracja 2: Wdrożenie PWA i Pamięci Offline (IndexedDB)
*   Konfiguracja Service Workera oraz manifestu PWA w `rae-portal`.
*   Dodanie obsługi IndexedDB do zapisywania lokalnego stanu sesji.

### Iteracja 3: Rejestracja Metryk Cache-Bustera i Zakończenie Wdrożenia
*   Dodanie automatycznego haszowania zasobów podczas budowania dystrybucji Windows.
*   Weryfikacja wydajności na słabym urządzeniu testowym (cel: czas ładowania UI < 1.5s na sieci 3G/lokalnym procesorze mobile).

---

## 7. Integracja i Wizualizacja Wymogów Zgodności (ISO 27001 & ISO 42001)

Ujednolicony interfejs webowy bezpośrednio odzwierciedla i wizualizuje mechanizmy zgodności z normami ISO wdrożone w silniku RAE. Poniższa tabela przedstawia mapowanie tych funkcji (Kto, Co, Dlaczego, Koszt i Efekt) oraz sposób ich prezentacji w UI:

| Funkcja ISO | Kto i Co Zrobił | Dlaczego (Cel) | Koszt Wdrożenia | Efekt Systemowy | Wizualizacja w UI |
|---|---|---|---|---|---|
| **Refaktoryzacja Baz Danych (ISO 42001 Lineage)** | **Grzegorz Leśniowski & Antigravity Core:** Wyodrębniono kolumny `session_id`, `project`, `source`, `ttl` z JSONB do indeksowanych kolumn Postgres. | Spowolnienie Dashboardu przez brak indeksów na JSONB oraz potrzeba jawnego śledzenia pochodzenia danych (provenance) do audytu retencji AI. | Stworzenie migracji Alembic phase4, dostosowanie `PostgreSQLStorage` i modelu memories. | Czas zapytania na Dashboardzie spadł z 3.5s do 0.2s (indeksy B-Tree). Pełna zgodność lineage. | **Decision Lineage Audit Trail:** Tabela w widoku "Audit & Decision Ledger" pokazująca historię i źródła każdego zapisanego wspomnienia. |
| **Automatyczne Wycofanie i Kwarantanna (ISO 27001 ISMS)** | **Antigravity Core:** Wdrożenie `RollbackManager` i stanów `IncidentScope` (LOCAL, SERVICE_GROUP, GLOBAL). | Zapewnienie ciągłości działania (Business Continuity) i automatyczne usuwanie skutków awarii bez udziału człowieka. | Asynchroniczna maszyna stanów, integracja z git-worktree oraz przywracanie kolekcji Qdrant z migawek. | Czas przywrócenia sprawności kontenera/kodu spadł poniżej 15-60 sekund w pełnej kwarantannie. | **SLA Rollback Monitors:** Liczniki czasu rzeczywistego w UI pokazujące czas do automatycznego restartu/przywrócenia w przypadku incydentu. |
| **Izolacja Danych Niejawnych (ISO 27001 & ISO 42001 Security)** | **Antigravity Core:** Blokady w `RAECoreService` niepozwalające danym oznaczonym jako `RESTRICTED` opuścić warstwy `Working`. | Zapobieganie wyciekom kluczy API, tokenów i danych poufnych klientów do publicznych repozytoriów open-source. | Opracowanie mechanizmu filtrowania i autoryzacji `_enforce_security_policy` w potoku pamięci. | Bezpieczna ekstrakcja pomysłów przez warstwę `Reflective` (dane open-source) bez ryzyka wycieku surowych sekretów. | **Information Classification Badges:** Kontenery i zasoby w UI są otagowane kolorami bezpieczeństwa (`RESTRICTED` - czerwony, `INTERNAL` - niebieski). Wyświetlanie ostrzeżeń przy próbie naruszenia zasad. |
