# Plan Naprawy i Perfekcyjnej Realizacji Systemu Zaawansowanych Testów i Jakości

Na podstawie audytu wdrożenia: `docs/mierzenie-rzeczywistej-jakosci-kodu.md` oraz `docs/PLAN_WDROZENIA_ZAAWANSOWANYCH_TESTOW_I_JAKOSCI.md`  
Data: 12 października 2026  
Status: W realizacji (/goal)  

---

## 1. Wyniki Dogłębnego Audytu (Luki do perfekcji)

Chociaż faza fundamentów została zrealizowana, audyt wykazał następujące braki względem pełnej specyfikacji dokumentu:

1. **Brak natywnego klienta SonarQube w `RAE-Quality`**:
   - *Stan zastany*: Wskaźnik `RC-07` korzystał z symulowanej wartości; silnik SAST opierał się wyłącznie na lokalnym Bandicie.
   - *Wymóg*: Działający na porcie 9000 SonarQube posiada 5 zarejestrowanych projektów (`backend`, `editornext`, `editor-backend`, `next-frontend`, `next-manager`). `RAE-Quality` musi bezpośrednio odpytywać API SonarQube z uwierzytelnianiem tokenem (`squ_...`) o status Quality Gate i liczbę podatności.

2. **Niepełny model metryk defektów (DORA Change Failure Rate)**:
   - *Stan zastany*: `DefectMetrics` zawierało `defect_escape_rate`, `severity_weighted_score`, `regression_rate`, ale brakowało wprost `change_failure_rate` (zdefiniowanego w punkcie 6 dokumentu źródłowego).
   - *Wymóg*: Uzupełnienie modelu i mechanizmu wyliczania o `Change Failure Rate (%)`.

3. **Brak sformalizowanego zestawu projektów referencyjnych (Golden Set DTP)**:
   - *Stan zastany*: `PDFDtpValidator` weryfikował pojedyncze specyfikacje dokumentów przekazane w payloadzie.
   - *Wymóg*: Utworzenie dedykowanego runnera `GoldenSetRunner` z bazą 5 kluczowych typów produktów poligraficznych (Wizytówka, Ulotka A5, Plakat B2, Opakowanie FEFCO z wykrojnikiem, Kalendarz trójdzielny) do testowania regresji DTP.

4. **Brak predykcyjnego wyboru testów (Predictive Test Selection z `RAE-Phoenix`)**:
   - *Stan zastany*: Mechanizm strefy wpływu był opisany w dokumencie, lecz nie był połączony programowo w `RiskCoverageEngine`.
   - *Wymóg*: Dodanie metody `get_predictive_test_plan(modified_files)`, która pyta `RAE-Phoenix` (`/v2/phoenix/impact`) o zależne symbole i mapuje je na konkretne ścieżki ryzyka (RC-01 do RC-08).

---

## 2. Plan Działań Naprawczych (Kroki do 100% Perfekcji)

### Krok 1: Implementacja `SonarQubeClient` w `packages/rae-quality/engines/security/`
- Utworzenie klienta HTTP z obsługą autoryzacji tokenem `squ_1111222233334444555566667777888899990000`.
- Odpytywanie endpointów `/api/qualitygates/project_status` oraz `/api/issues/search` dla projektów `editornext` i `backend`.
- Wstrzyknięcie rzeczywistych wyników SonarQube do ścieżki `RC-07`.

### Krok 2: Uzupełnienie modelu `DefectMetrics` o `Change Failure Rate`
- Dodanie `change_failure_rate: float` do `models/risk.py`.
- Aktualizacja `DefectTracker.calculate_metrics()` o wyliczanie wskaźnika wdrożeń zakończonych niepowodzeniem/interwencją.

### Krok 3: Implementacja `GoldenSetRunner` w `packages/rae-quality/engines/testing/`
- Zdefiniowanie 5 kanonicznych specyfikacji projektów DTP.
- Automatyczne uruchamianie walidacji całej paczki i wyliczanie zbiorczego wskaźnika regresji dokumentów produkcyjnych dla `RC-02`.

### Krok 4: Integracja z `RAE-Phoenix` dla Predykcyjnego Wyboru Testów
- Implementacja `predictive_test_selection` w `RiskCoverageEngine`, łączącego listę zmienionych plików z analizą grafu zależności Phoenixa i rekomendacją wymaganych testów.

### Krok 5: Weryfikacja Testami, Aktualizacja Kontenera i Git Flow
- Dodanie testów jednostkowych dla nowych modułów (`test_sonar_client.py`, `test_golden_set.py`).
- Przebudowa kontenera `rae-quality`, weryfikacja na żywo na porcie 8010.
- Aktualizacja skryptu CLI `scripts/run_advanced_quality_audit.py`.
- Złożenie i wypchnięcie zmian do GitHub zgodnie z Git Flow.
