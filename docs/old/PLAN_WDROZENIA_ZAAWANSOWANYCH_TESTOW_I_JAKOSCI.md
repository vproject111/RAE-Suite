# Plan Wdrożenia Zaawansowanych Testów i Pomiaru Jakości (Dreamsoft & RAE-Suite)

Na podstawie: `mierzenie-rzeczywistej-jakosci-kodu.md`  
Data utworzenia: 12 października 2026  
Status: W realizacji  
Właściciel: Silicon Oracle RAE Suite & Dreamsoft Architecture Team  

---

## 1. Cel Strategiczny i Architektura

Celem jest wdrożenie wielowymiarowego systemu pomiaru rzeczywistej jakości kodu i ryzyka biznesowego w miejsce prostego wskaźnika Code Coverage. System integruje:
1. Istniejące testy kalkulatora cen, formatów i checkoutu w `dreamsoft_factory`.
2. Istniejące testy siatek opakowań, DTO i potoku produkcyjnego w `editornext`.
3. Narzędzia analizy statycznej: **SonarQube** (port 9000).
4. Centralny agregator i bramkę decyzyjną: **RAE-Quality** (port 8010) we współpracy z **RAE-Phoenix** (port 8012).

---

## 2. Macierz Ryzyka Biznesowego (Risk Matrix)

Kluczowy wskaźnik obliczany jest według wzoru:
$$RiskCoverage = \frac{\sum (w_i \cdot c_i)}{\sum w_i} \times 100\%$$

| ID | Ścieżka / Proces Biznesowy | System | Waga ($w_i$) | Klasa Ryzyka | Wymagany Typ Testu |
|:---|:---|:---:|:---:|:---:|:---|
| **RC-01** | Kalkulacja cen i matryce formatów (A4, A5, nakłady) | Dreamsoft | 10 | P0 (Krytyczne) | Cold calc exhaustive, matrix test |
| **RC-02** | Geometria i eksport PDF produkcyjnego (TrimBox, Bleed, CMYK) | NextEditor | 10 | P0 (Krytyczne) | Walidator geometrii PDF DTP, Preflight |
| **RC-03** | Zapis, odczyt i migracja projektów (Scene Graph JSON) | NextEditor | 10 | P0 (Krytyczne) | Snapshoty integralności sceny E2E |
| **RC-04** | Składanie zamówienia i checkout (koszyk, kupony, płatność) | Dreamsoft | 9 | P0 (Krytyczne) | E2E Playwright full flow |
| **RC-05** | Złożone konstrukcje (Opakowania ECMA/FEFCO, Fotoalbumy) | NextEditor | 8 | P1 (Wysokie) | Testy kinematyki 3D i linii cięcia |
| **RC-06** | Wydajność silnika kalkulacji ($T_{calc} < 200$ ms) | Obie | 7 | P1 (Wysokie) | Benchmark stopwatch, pomiary p95 |
| **RC-07** | Bezpieczeństwo, autoryzacja i ochrona danych (SAST/OWASP) | Całość | 8 | P1 (Wysokie) | SonarQube, Enterprise Guard |
| **RC-08** | Regresja wizualna UI i layoutu edytora | Frontend | 4 | P2 (Średnie) | Porównanie migawek pikselowych |

---

## 3. Fazy Implementacji

### Faza 1: Konsolidacja i Automatyzacja Testów Krytycznych (RC-01, RC-04, RC-06)
- Utworzenie ujednoliconego modułu weryfikacji kalkulatora cenowego i procesów zamówień (`engines/testing/calculator_verifier.py`).
- Implementacja automatycznego pomiaru czasu kalkulacji (stopwatch p95).
- Obsługa produktów kluczowych: Wizytówki, Ulotki, Plakaty, Banery, Katalogi.

### Faza 2: Walidator DTP i Regresja Dokumentów Produkcyjnych (RC-02, RC-05)
- Implementacja silnika analizy struktury PDF produkcyjnego (`engines/testing/pdf_dtp_validator.py`):
  - Weryfikacja wymiarów netto/brutto (`TrimBox`, `BleedBox`, `MediaBox`).
  - Sprawdzanie osadzenia fontów (brak brakujących glifów).
  - Weryfikacja czystego kanału K dla drobnych tekstów typograficznych.
  - Sprawdzanie warstw technicznych (wykrojnik, lakier UV, biały poddruk) jako Spot Colors z atrybutem Overprint.
- Stworzenie zestawu referencyjnych specyfikacji projektów (*Golden Set Specifications*).

### Faza 3: Integracja z SonarQube i Telemetrią Defektów (RC-07)
- Integracja `RAE-Quality` z działającym serwerem SonarQube (port 9000).
- Wdrożenie modułu zbierania i klasyfikacji defektów produkcyjnych (Defect Escape Rate, Severity-Weighted Defects, MTTR).

### Faza 4: Dynamiczny Risk Coverage i Tribunal Deployment Gate
- Rozszerzenie `packages/rae-quality`:
  - Endpoint `/v2/quality/risk-coverage` (obliczający rzeczywiste ważone pokrycie ryzyka).
  - Endpoint `/v2/quality/gate-decision` (trzystopniowa bramka wdrożeniowa: Zezwól / Wymaga akceptacji / Blokada).
  - MCP narzędzia w `rae-quality`: `get_risk_coverage`, `evaluate_deployment_gate`, `run_pdf_dtp_audit`.
- Integracja z `RAE-Phoenix` (analiza Impact Zone pod kątem predykcyjnego uruchamiania testów).

---

## 4. Kryteria Sukcesu i Progi Quality Gate

| Poziom Decyzji | Warunki Techniczne | Rezultat CI/CD |
|:---|:---|:---|
| **POZIOM 1: ZEZWOLENIE** | $RiskCoverage \ge 95\%$, brak jakichkolwiek błędów P0/P1, zero podatności krytycznych w SonarQube | Automatyczne wdrożenie na środowisko docelowe |
| **POZIOM 2: OSTRZEŻENIE** | $RiskCoverage \in [85\%, 95\%)$, drobne błędy P2/P3, brak wpływu na finanse, ceny i pliki PDF | Wymagana ręczna autoryzacja Tech Leada |
| **POZIOM 3: BLOKADA** | Dowolny błąd P0 (rozjazd cen, błąd geometrii PDF, uszkodzenie zapisu sceny), $RiskCoverage < 85\%$ | Całkowita blokada pipeline'u wdrożeniowego |
