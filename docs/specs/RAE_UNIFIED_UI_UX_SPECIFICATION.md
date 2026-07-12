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

### Elementy Integracyjne:
1.  **Monitor Pracy Agentów (Gantt Live-view):** Pokazuje, który moduł aktualnie wykonuje zadanie w piaskownicy w czasie rzeczywistym (Phoenix analizuje, Hive odpala testy, Quality przeprowadza sąd 3-warstwowy).
2.  **Cognitive Space Explorer:** Interaktywna wizualizacja grafu pamięci semantycznej z możliwością przeszukiwania i ręcznej edycji wspomnień.
3.  **Audit & Decision Ledger View:** Tabela pokazująca podpisane dowody decyzji (SLA wycofań, `@audited_operation` oraz statusy poprawek).

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
