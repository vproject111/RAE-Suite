# PLAN POPRAWY I PERFEKCYJNEGO WDROŻENIA RAE-QUALITY 2.0

> **Dokument**: Audyt weryfikacyjny i plan doprowadzenia wdrożenia [`poziom-bezpieczeństwa-kodu.md`](./poziom-bezpieczeństwa-kodu.md) do 100% perfekcji architektonicznej, funkcjonalnej i operacyjnej.
> **Moduł docelowy**: `RAE-Suite/packages/rae-quality`
> **Status docelowy**: 6 kompletnych silników, 219 aktywnych reguł (198 katalog + 12 AI/SaaS + 9 `RAE-EDITOR-SECURITY`), pełna obsługa Baseline / Phased Rollout, AST Test Integrity Guard, 100% zielonych testów w kontenerze produkcyjnym i synchronizacja Harbor + Git Flow.

---

## 1. Wyniki szczegółowego audytu obecnego wdrożenia

Po dokładnym porównaniu bieżącego kodu w `packages/rae-quality` z wszystkimi 13 sekcjami dokumentu [`poziom-bezpieczeństwa-kodu.md`](./poziom-bezpieczeństwa-kodu.md) zidentyfikowano 6 obszarów wymagających uzupełnienia do pełnej perfekcji:

| ID | Obszar z dokumentu | Zidentyfikowana luka / możliwość ulepszenia | Docelowe rozwiązanie |
| :--- | :--- | :--- | :--- |
| **G1** | **Sekcja 1 i 3**: 6 silników architektury (`AI Review Engine` + kontrole semantyczne AI) | Zaimplementowano 5 silników (`Policy`, `Security`, `CodeQuality`, `Architecture`, `Infrastructure`) oraz `AutoRepairOrchestrator`, ale brakowało wydzielonego, szóstego silnika `AIReviewEngine` (`engines/governance/ai_review_engine.py`) realizującego semantyczną analizę ścieżek autoryzacji właściciela projektu, granic tenantów, ról administratora drukarni i logiki zamówień wraz z generowaniem twardych dowodów (`EvidenceItem`). | Utworzenie [`engines/governance/ai_review_engine.py`](../packages/rae-quality/engines/governance/ai_review_engine.py) i wpięcie go do [`RAEQualityGatewayV2`](../packages/rae-quality/engines/governance/quality_gateway_v2.py). |
| **G2** | **Sekcja 4**: Zestaw 9 reguł `RAE-EDITOR-SECURITY` (`RAE-EDT-001` .. `RAE-EDT-009`) | W katalogu reguł zdefiniowano wszystkie 9 reguł `RAE-EDT-001..009`, jednak w skanerze `SecurityGateway` aktywne detektory istniały tylko dla `RAE-EDT-002` i `RAE-EDT-005`. Brakowało aktywnych detektorów dla pozostałych 7 reguł edytora (`RAE-EDT-001`, `003`, `004`, `006`, `007`, `008`, `009`). | Rozbudowa [`SecurityGateway`](../packages/rae-quality/engines/security/security_gateway.py) o komplet detektorów dla wszystkich 9 reguł `RAE-EDITOR-SECURITY` (w tym podmiana produkcyjnego PDF, EXIF GPS, limity kosztów AI, dostęp admina drukarni, brak autoryzacji zasobu/strony). |
| **G3** | **Sekcja 2 i 4**: Reguły P0 `Security & OWASP` oraz `Identity & Secrets` (1–40) | Skaner wykrywał SQLi, XSS, SSRF, IDOR, Path Traversal, Mass Assignment i sekrety, ale nie posiadał aktywnych reguł detekcji dla: `CSRF` (`RAE-SEC-003`), niebezpiecznego `CORS` z poświadczeniami (`RAE-SEC-004`), `Clickjacking/CSP` (`RAE-SEC-009/010`), słabego hashowania haseł `MD5/SHA1` zamiast `bcrypt/Argon2` (`RAE-SEC-023`), `JWT` bez wygasania/`alg:none` (`RAE-SEC-024`), `Timing Attacks` (`RAE-SEC-032`) oraz braku weryfikacji podpisu `Webhook Signature` (`RAE-SEC-034`). | Dodanie deterministycznych detektorów dla `RAE-SEC-003`, `004`, `010`, `023`, `024`, `032`, `034` w [`SecurityGateway`](../packages/rae-quality/engines/security/security_gateway.py). |
| **G4** | **Sekcja 10**: Stan bazowy (Baseline Debt) i stopniowe włączanie bramek (Etapy I–IV) | Dokument wyraźnie wymaga (linia 717): *„Najpierw należy ustalić stan bazowy istniejących repozytoriów, wyeliminować fałszywe alarmy i stopniowo włączać bramki dla nowego kodu. Inaczej agenci mogą utknąć na setkach historycznych problemów niezwiązanych z aktualną zmianą.”* | Dodanie w [`PolicyEngine`](../packages/rae-quality/engines/policy/policy_engine.py) oraz [`RAEQualityGatewayV2`](../packages/rae-quality/engines/governance/quality_gateway_v2.py) mechanizmu **Baseline & Rollout Filter**, który oddziela błędy wprowadzone w aktualnej zmianie (blokujące) od historycznego długu bazowego (`baseline_fingerprints`) oraz obsługuje 4 etapy wdrożenia (`etap_1_p0` .. `etap_4_prod`). |
| **G5** | **Sekcja 9**: Ochrona testów przed osłabianiem (`TestIntegrityGuard` AST) | W repozytorium znajduje się moduł AST [`src/test_integrity_guard.py`](../packages/rae-quality/src/test_integrity_guard.py) wykrywający usunięcie asercji oraz podmianę asercji na `assert True` / `assert 1 == 1`. Należy połączyć go bezpośrednio z `CodeQualityEngine.verify_fix()`. | Integracja `TestIntegrityGuard` wewnątrz [`CodeQualityEngine.verify_fix`](../packages/rae-quality/engines/testing/code_quality_engine.py), aby każda próba zmniejszenia liczby asercji lub użycia `assert True` była natychmiast blokowana (`BLOCK`). |
| **G6** | **Infrastruktura, Harbor i Git Flow**: Synchronizacja obrazu z najnowszym stanem po scaleniu `main` | Po scaleniu `main` z `develop` doszedł plik `src/test_integrity_guard.py`. Należy przebudować obraz produkcyjny ze wszystkimi ulepszeniami G1–G5, wypchnąć na Harbor, odtworzyć kontener lokalny, wyczyścić cache i zsynchronizować `develop` oraz `main` w `RAE-Quality` i `RAE-Suite`. | Pełny build obrazu produkcyjnego, push na Harbor (`2.9.0`, `2.9.2`, `latest`), restart kontenerów, czyszczenie cache i 4-fazowy Git Flow. |

---

## 2. Plan realizacji (4 kroki wykonawcze)

### Krok 1: Utworzenie 6. silnika `AIReviewEngine` (`engines/governance/ai_review_engine.py`)
- Semantyczna kontrola ścieżek autoryzacji (`owner_id`, `tenant_id`, `printshop_id`), weryfikacja dostępu administratora drukarni do projektu klienta z wymogiem śladu audytowego (`RAE-EDT-003`) oraz kontrola integralności logiki zamówień (`RAE-SEC-202`).
- Automatyczne generowanie ustrukturyzowanych dowodów `EvidenceItem` i odrzucanie zmian pozbawionych weryfikowalnego dowodu.

### Krok 2: Rozbudowa `SecurityGateway` o pełne pokrycie `RAE-EDITOR-SECURITY` (9/9) oraz OWASP/Identity (`CSRF`, `CORS`, `CSP`, `bcrypt/Argon2`, `JWT`, `Timing Attacks`, `Webhook HMAC`)
- Dodanie reguł detekcyjnych dla `RAE-EDT-001`, `RAE-EDT-003`, `RAE-EDT-004`, `RAE-EDT-006`, `RAE-EDT-007`, `RAE-EDT-008`, `RAE-EDT-009`.
- Dodanie reguł detekcyjnych dla `RAE-SEC-003`, `RAE-SEC-004`, `RAE-SEC-010`, `RAE-SEC-023`, `RAE-SEC-024`, `RAE-SEC-032`, `RAE-SEC-034`.

### Krok 3: Wdrożenie `Baseline & Phased Rollout Manager` oraz integracja AST `TestIntegrityGuard`
- Rozbudowa `CodeQualityEngine.verify_fix` o weryfikację AST przez `TestIntegrityGuard` (blokada spadku liczby asercji i `assert True`).
- Dodanie w `PolicyEngine` i `RAEQualityGatewayV2` filtrowania `baseline_fingerprints` (odróżnianie nowego kodu od historycznego długu technicznego) oraz profili etapowych (`etap_1` .. `etap_4`).

### Krok 4: Testy weryfikacyjne, obraz produkcyjny, Harbor, czyszczenie cache i Git Flow
- Dodanie zestawu testów `tests/test_perfection_upgrade_v2.py` weryfikującego wszystkie punkty G1–G5.
- Zbudowanie obrazu produkcyjnego, wypchnięcie na Harbor (`harbor.cloud.printworks.pl/dreamsoft/rae-quality:2.9.0`, `2.9.2`, `latest`), przeładowanie lokalnego kontenera, wyczyszczenie cache i pełny 4-fazowy Git Flow.
