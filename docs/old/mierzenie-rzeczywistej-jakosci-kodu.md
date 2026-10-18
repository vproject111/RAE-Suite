mierzenie rzeczywistej jakości aplikacji i ryzyka biznesowego.
W przypadku Waszych projektów — Dreamsoft, RAE-Suite i nowego edytora NextEditor — proponowałbym zbudowanie wspólnego systemu kontroli jakości, zintegrowanego z GitHub, SonarQube i procesem wdrażania.
1. Pokrycie ryzyka (Risk Coverage)
To coś więcej niż standardowe pokrycie kodu testami (Code Coverage).
Przykładowo: 90% pokrycia kodu nie oznacza, że aplikacja jest bezpieczna, jeśli nie przetestowano prawidłowo obliczania ceny, zapisywania projektu czy generowania pliku PDF do druku.
Najważniejsze narzędzia:
Narzędzie	Zastosowanie
SonarQube	Pokrycie kodu, błędy, podatności, złożoność
Allure TestOps	Zarządzanie testami, ich historią i wynikami
ReportPortal	Analiza nieudanych testów, grupowanie awarii
Launchable	Priorytetyzacja testów na podstawie zmian i historii
OWASP ZAP	Automatyczne wykrywanie zagrożeń bezpieczeństwa
Żadne z tych narzędzi samodzielnie nie zna wszystkich krytycznych procesów biznesowych. Trzeba zdefiniować je w aplikacji i powiązać z testami.
Przykład dla NextEditor
Ścieżka krytyczna	Ryzyko	Wymagane testy
Zapis i ponowne otwarcie projektu	Krytyczne	E2E, integracyjne
Generowanie PDF do druku	Krytyczne	Porównanie PDF, geometria, fonty
Obliczanie ceny produktu	Krytyczne	Jednostkowe, kontraktowe
Produkty złożone (fotoalbum, FEFCO)	Krytyczne	Geometria, E2E
Generowanie kalendarium	Wysokie	Daty, święta, języki
Generowanie teł i layoutów	Średnie	Wizualne, funkcjonalne
Zmiana koloru interfejsu	Niskie	Wizualne
Można następnie zbudować wskaźnik:
\[
RiskCoverage=\frac{\sum(w_i\cdot c_i)}{\sum w_i}\times100\%
\]

gdzie \(w_i\) oznacza wagę ryzyka danej ścieżki, a \(c_i\) stopień jej zweryfikowania testami.
To będzie znacznie bardziej użyteczna metryka niż sam Code Coverage.
2. Defekty uciekające na produkcję (Defect Escape Rate)
Tutaj interesuje nas, ile błędów przeszło przez testy i zostało wykrytych dopiero przez użytkowników lub monitoring produkcyjny.
Narzędzia, które warto rozważyć:
Narzędzie	Co wykrywa
Sentry	Błędy JavaScript, PHP, Node.js, stack trace, regresje
GlitchTip	Monitoring wyjątków, alternatywa self-hosted dla Sentry
Grafana + Loki	Logi, błędy i anomalie systemowe
OpenTelemetry	Śledzenie błędów przez frontend, API i backend
Jira / GitHub Issues	Klasyfikacja defektów, ich źródła i dotkliwości
Metryki, które warto zbierać
Defect Escape Rate
8%
Przykład: 8 z 100 defektów wykryto dopiero na produkcji
Regresje produkcyjne
3
Przykładowa liczba błędów powracających po wdrożeniu
MTTR
2,5 h
Przykładowy średni czas przywrócenia działania
Defekty krytyczne
1
Przykładowa liczba defektów klasy P0/P1

Wartości ilustracyjne — nie są to wyniki Waszych aplikacji.
Ważne, aby defekty klasyfikować według rzeczywistej dotkliwości:
- P0: utrata projektów, błędne pliki produkcyjne na dużą skalę, poważny incydent bezpieczeństwa.
- P1: błędna kalkulacja ceny, niedziałający zapis projektu, uszkodzony eksport.
- P2: awaria pojedynczej funkcji z możliwością obejścia.
- P3: błędy kosmetyczne i drobne problemy UX.
Dla Waszej działalności jeden błąd P0 może być bardziej kosztowny niż kilkaset błędów P3. Dlatego sam licznik defektów nie wystarcza.
3. Regresja — wykrywanie błędów po zmianach
Tutaj zastosowałbym trzy rodzaje testów.
Rodzaj regresji	Narzędzia	Co sprawdzamy
Funkcjonalna	Playwright	Czy istniejące funkcje nadal działają
Wizualna	Argos CI lub Playwright	Czy zmienił się wygląd projektu
Wydajnościowa	k6 + Grafana	Czy aplikacja nie zwolniła
Produkcyjna	Sentry	Czy naprawiony błąd powrócił
Playwright potrafi zapisywać przebieg nieudanych testów, stan strony, żądania sieciowe oraz różnice między obrazami. 

GitHub
+1




Sentry rozpoznaje ponowne wystąpienie naprawionego błędu w nowszej wersji aplikacji, pod warunkiem poprawnego oznaczania wydań. 

Sentry Help Center
+1




Dla edytora szczególnie istotna jest jeszcze regresja dokumentów produkcyjnych.
Przykładowo, po zmianie silnika renderującego automatyczny test powinien otworzyć 100 referencyjnych projektów, wygenerować PDF-y i sprawdzić, czy nie zmieniły się pozycje obiektów, wymiary, spady, fonty, kolory oraz zawartość stron. Same porównania pikselowe nie wystarczą — potrzebna jest także walidacja struktury i geometrii PDF.
4. Jak połączyłbym to w Waszym środowisku

Moja propozycja to wykorzystać narzędzia, które już macie, i dołożyć tylko brakujące elementy.
Warstwa	Propozycja
Analiza kodu	Istniejący SonarQube
Testy E2E i regresja	Playwright
Analiza wyników testów	ReportPortal (self-hosted)
Defekty produkcyjne	Sentry
Monitoring	Grafana + OpenTelemetry
Zarządzanie defektami	GitHub Issues
Raport jakości	Własny dashboard RAE-Quality
ReportPortal oferuje m.in. historię uruchomień, trendy awarii i identyfikację niestabilnych testów. 

ReportPortal Documentation
+1




5. Najważniejszy element: automatyczna decyzja o wdrożeniu
Wprowadziłbym trzy poziomy decyzji:
Wdrożenie dozwolone — wszystkie testy krytyczne zaliczone, brak nowych poważnych problemów.


Wymaga akceptacji — niewielkie regresje lub niepełne pokrycie obszarów średniego ryzyka.


Blokada wdrożenia — nieudany test krytyczny, wykryta utrata danych, błąd geometrii produkcyjnej albo poważna podatność.


Takie bramki powinny być wdrażane stopniowo, żeby niestabilne testy nie blokowały niepotrzebnie całego rozwoju.
6. Co mierzyłbym w RAE-Quality?
Proponuję sześć podstawowych wskaźników:
1. Risk Coverage — procent ważonego ryzykiem pokrycia ścieżek krytycznych.
2. Defect Escape Rate — odsetek defektów wykrytych dopiero na produkcji.
3. Severity-Weighted Defects — liczba defektów z uwzględnieniem ich dotkliwości.
4. Regression Rate — udział zmian lub wydań powodujących regresję.
5. Change Failure Rate — procent wdrożeń wymagających interwencji z powodu awarii.
6. MTTR — średni czas przywrócenia działania po incydencie.
Ważne: nie wszystkie te wskaźniki da się wyliczyć wyłącznie z kodu i automatycznych testów. Potrzebna jest ewidencja incydentów oraz powiązanie ich z wydaniami.
Wniosek: nie kupowałbym jednego dużego komercyjnego systemu QA. Zbudowałbym wspólną warstwę pomiarową nad SonarQube, Playwright, ReportPortal i Sentry, wykorzystując RAE-Quality jako centralny dashboard.
Dzięki temu można porównywać jakość Dreamsoft, RAE i NextEditor według tych samych zasad, ale z osobnymi definicjami krytycznych procesów.
Najciekawsze byłoby pójście jeszcze dalej: powiązać analizę zmian w GitHub z mapą ryzyka aplikacji, tak aby przed każdym wdrożeniem system wskazywał, które procesy biznesowe mogą zostać uszkodzone i jakie testy należy uruchomić. To byłoby rzeczywiste zarządzanie ryzykiem zmian, a nie tylko kolejne raportowanie pokrycia kodu.
