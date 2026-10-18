Tak — zrobiłbym to iteracyjnie, z działającym systemem po każdej iteracji, zamiast wdrażać cały Adaptive Evidence Retrieval jednym dużym zadaniem. Kluczowa zasada: każda iteracja musi dać mierzalny efekt, mieć feature flag, test regresji i możliwość prostego wycofania. Artykuł sam wskazuje, że różne architektury RAG rozwiązują różne źródła błędów, więc nie ma sensu wdrażać wszystkich naraz.

Iteracyjny plan wdrożenia RAE Adaptive Evidence Retrieval
Iteracja	Zakres	Efekt końcowy	Ryzyko
0	Baseline + benchmark	wiemy, czy kolejne zmiany faktycznie poprawiają retrieval	bardzo małe
1	ContextEnvelope	pamięć zna pochodzenie i kontekst informacji	małe
2	EvidencePackage	ujednolicony wynik retrievalu z provenance	małe
3	Evidence Sufficiency Gate	RAE rozpoznaje słaby retrieval	małe/średnie
4	Adaptive Retrieval 2-pass	RAE potrafi wyszukać ponownie	średnie
5	Query classification/routing	różne pytania używają różnych strategii	średnie
6	GraphRAG-lite	graf uzupełnia retrieval o relacje	średnie
7	Graph communities + Reflection	pełniejsze pytania przekrojowe	średnie
8	Multimodal RAG	screenshoty/PDF/diagramy stają się wiedzą	średnie
9	RAE-Lab adaptive tuning	automatyczne strojenie retrievalu	większe
10	produkcyjne rollout + self-improvement	system uczy się na własnych błędach	kontrolowane
Iteracja 0 — Retrieval Baseline

Cel: zanim cokolwiek zmienimy, ustalić rzeczywistą jakość obecnego HybridSearchEngine.

RAE już wykonuje strategie wyszukiwania równolegle, scala wyniki i może uruchomić reranker. Tego na razie nie ruszamy.

Implementacja

Dodać np.:

rae-core/rae_core/evaluation/retrieval_benchmark.py
rae-core/rae_core/evaluation/golden_queries.py
tests/retrieval/golden/

Każdy przypadek:

{
  "query": "Where is HybridSearchEngine instantiated?",
  "type": "CODE_RELATION",
  "expected_sources": [
    "apps/memory_api/services/rae_core_service.py"
  ]
}

Kategorie benchmarku:

exact_identifier
code_symbol
semantic_code
historical_decision
cross_file
cross_repository
temporal
multi_source
graph_relation
Metryki

Minimum:

Recall@5
Recall@10
MRR
NDCG@10

p50
p95

reranker_gain
empty_result_rate
wrong_tenant_results
Definition of Done
≥ 200 realnych golden queries
benchmark uruchamiany z CLI
wynik zapisywany JSON
CI potrafi wykryć regresję

Nic jeszcze nie zmieniamy w produkcyjnym retrievalu.

Iteracja 1 — ContextEnvelope

To pierwsza rzeczywista poprawa.

Contextual RAG według materiału rozwiązuje problem fragmentów pozbawionych informacji, z jakiego dokumentu i sytuacji pochodzą.

Cel

Z:

"enable_reranking defaults to false"

zrobić wiedzę:

repository: RAE-agentic-memory
file: rae-core/rae_core/search/engine.py
class: HybridSearchEngine
symbol: search
commit: ...
context:
configuration of optional retrieval reranking
Ważne

Nie zmieniamy raw content.

Obecny kod świadomie wyłączył wzbogacanie query, ponieważ „enrichment dilutes technical signal”.

To podejście zostaje.

Dodajemy:

RawMemory
    +
ContextEnvelope
Pierwsza wersja

Nie używałbym jeszcze LLM.

Context można generować deterministycznie z:

repo
branch
commit
file
language
class
function
source_type
project
task
trace
timestamp
Feature flag
RAE_CONTEXT_ENVELOPE_ENABLED=false
DoD

Benchmark:

baseline Recall@10
vs
ContextEnvelope Recall@10

Wymaganie:

nie pogorszyć exact lookup
poprawić semantic/cross-file retrieval

Jeśli nie poprawia — iteracja nie przechodzi dalej.

Iteracja 2 — EvidencePackage

Tutaj jeszcze bez agentowego ponownego wyszukiwania.

Problem

Dzisiaj agent dostaje przede wszystkim uporządkowane wyniki wyszukiwania.

Docelowo powinien dostać:

co znaleziono
skąd to pochodzi
dlaczego zostało wybrane
jaką strategią
jak bardzo temu ufamy
czy źródła sobie przeczą
Model
class EvidenceItem:
    memory_id: UUID
    content: str

    score: float
    trust_score: float

    strategy: str

    repository: str | None
    commit_sha: str | None
    file_path: str | None

    timestamp: datetime | None


class EvidencePackage:
    query: str

    items: list[EvidenceItem]

    strategies_used: list[str]

    confidence_score: float

    missing_aspects: list[str]
    contradictions: list
Kluczowa własność

Phoenix, agent lub LLM powinien później konsumować:

EvidencePackage

a nie znać internals:

Qdrant
Postgres FTS
GraphTraversalStrategy
reranker

To bardzo dobrze oddzieli retrieval od reasoning.

DoD

Obecny retrieval:

query → HybridSearchEngine

i nowy:

query → HybridSearchEngine → EvidencePackage

muszą zwracać te same dokumenty dla feature flag OFF/compatibility mode.

Iteracja 3 — Evidence Sufficiency Gate

To pierwszy element prawdziwego Agentic RAG.

Materiał opisuje Agentic RAG jako system, który po wyszukiwaniu ocenia, czy wynik wystarcza, a gdy nie — szuka ponownie.

Na tym etapie robimy tylko:

search
  ↓
EvidencePackage
  ↓
SUFFICIENT / INSUFFICIENT

Jeszcze bez retry.

EvidenceSufficiencyGate

Pierwsza wersja bez LLM.

score =
  relevance
+ coverage
+ diversity
+ trust
+ temporal consistency
- contradictions

Przykład:

relevance             30%
coverage              25%
source diversity      15%
trust                 15%
temporal consistency  15%
Co logujemy
retrieval_trace_id

evidence_score
coverage_score
relevance_score
contradictions
missing_aspects
decision
Shadow mode

Bardzo ważne:

RAE_EVIDENCE_GATE_MODE=shadow

Gate niczego jeszcze nie zmienia.

Tylko obserwujemy:

Czy przypadki oznaczone jako INSUFFICIENT rzeczywiście częściej kończą się błędną odpowiedzią?

DoD

Na golden queries trzeba osiągnąć sensowną korelację między:

low evidence score

a:

retrieval failure

Dopiero wtedy gate dostaje wpływ na wykonanie.

Iteracja 4 — Agentic Retrieval 2-pass

Teraz robimy właściwą pętlę:

query
 ↓
search
 ↓
Evidence Gate
 ├─ sufficient → done
 │
 └─ insufficient
        ↓
     rewrite
        ↓
      search
        ↓
       done
Tylko jeden retry

Pierwsza produkcyjna wersja:

max_passes = 2

Bez dyskusji.

Nie pozwalamy agentowi wykonać:

search → search → search → search → ...
QueryRewriter

Nie powinien „napisać ładniejszego promptu”.

Powinien odpowiedzieć:

{
  "missing_aspects": [
    "historical rationale"
  ],
  "queries": [
    "HybridSearchEngine enrichment decision",
    "technical signal query enrichment"
  ],
  "strategy_adjustments": {
    "fulltext": 1.4,
    "episodic": 1.3
  }
}
DoD

Osobny benchmark:

queries requiring multi-hop/multi-source

Porównujemy:

1-pass
vs
2-pass

Potrzebna jest wyraźna poprawa jakości, nie tylko większa liczba dokumentów.

Iteracja 5 — QueryClassifier i routing

Dopiero teraz warto automatycznie dobierać strategię.

Query types

Pierwsza wersja:

EXACT_IDENTIFIER
CODE
ARCHITECTURAL
HISTORICAL
TEMPORAL
RELATIONAL
MULTI_SOURCE
GENERAL
Przykład

Zapytanie:

CVE-2026-12345

może dostać:

FTS     0.70
Vector  0.20
Graph   0.10

A:

Dlaczego zmieniliśmy sposób budowania kontekstu?

raczej:

Vector      0.30
Graph       0.25
Episodic    0.30
Reflective  0.15
Najpierw rules

Nie zaczynałbym od LLM classifier.

Najpierw:

regex
query features
symbol detection
ID detection
language/code markers

LLM dopiero jako fallback.

DoD

Router musi poprawiać:

quality / latency / cost

w porównaniu z uruchamianiem wszystkich strategii zawsze.

Iteracja 6 — GraphRAG-lite

RAE posiada już GraphTraversalStrategy, który robi BFS po grafie od seed_ids.

Nie implementujemy jeszcze community detection.

Najpierw wykorzystujemy to, co jest.

Flow
Vector / FTS
     ↓
top seed memories
     ↓
GraphTraversalStrategy
     ↓
related memories
     ↓
Fusion

Czyli agent nie musi znać seed_ids.

System sam je generuje.

Przykład
HybridSearchEngine
      ↓
engine.py
      ↓
graph
 ├ rae_core_service.py
 ├ tests
 ├ interface
 └ architecture decision
DoD

Benchmark:

relationship questions
dependency questions
why/how questions
cross-file architecture

Jeżeli GraphRAG-lite nie daje zysku, nie budujemy jeszcze communities.

Iteracja 7 — Graph Communities + Reflective Memory

Dopiero tutaj przechodzimy do GraphRAG zbliżonego do opisu z materiału:

entities
→ relationships
→ communities
→ summaries
→ global retrieval

Community detection

Np.:

Leiden

albo początkowo prostsze connected/subgraph clustering.

Community przykładowo:

Hybrid Search subsystem

HybridSearchEngine
VectorSearchStrategy
FullTextStrategy
GraphTraversalStrategy
LogicGateway
Reranker
tests
configuration
Najważniejszy wybór

Community summary zapisujemy jako:

Reflective Memory

Nie budujemy osobnej bazy GraphRAG.

RAE ma już warstwę Reflective oraz graf wiedzy.

Incremental update

Nie:

rebuild whole graph

ale:

changed entity
 ↓
affected community
 ↓
dirty
 ↓
rebuild summary
DoD

Musi poprawić pytania typu:

Jak działa system pamięci RAE jako całość?

Jakie były główne problemy z retrievalu?

Jak zmieniał się subsystem X?

czyli pytania, na które pojedynczy chunk nie wystarcza.

Iteracja 8 — Multimodal Retrieval

Dopiero po stabilizacji tekstowego/graph retrieval.

Materiał zwraca uwagę, że OCR lub ekstrakcja tekstu mogą niszczyć tabele, wykresy i układ stron.

RAE ma szczególnie naturalne źródło danych:

RAE-Hive
+
Playwright
Zakres v1

Tylko:

Playwright screenshots
UI errors
architecture diagrams
PDF pages

Nie każde zdjęcie.

Model
Artifact
 ├ raw image
 ├ OCR text
 ├ visual embedding
 ├ text embedding
 └ ContextEnvelope
Strategia
VisualSearchStrategy

jako kolejna strategia używana przez istniejący system.

Nie osobne:

MultimodalRAESystem
DoD

Przypadki:

"na którym ekranie pojawił się ten błąd?"
"znajdź screenshot z uszkodzonym menu"
"w którym PDF jest ten diagram?"

muszą być odtwarzalne.

Iteracja 9 — RAE-Lab Retrieval Optimizer

Dopiero gdy mamy dane z poprzednich iteracji.

RAE-Lab posiada już mechanizmy Auto-Tuner/MAB i Shadow Evaluation.

Niech optymalizuje:

weights
top_k
reranker threshold
evidence threshold
retry threshold
graph depth
Reward

Nie:

highest similarity

ale:

answer_quality
- latency_penalty
- token_cost
- failed_retrieval

Czyli przykładowo:

reward =
    quality * 0.65
  - latency * 0.10
  - cost * 0.10
  - retrieval_failure * 0.15

RAE-Lab najpierw pracuje:

SHADOW

potem:

ADVISORY

dopiero potem:

ACTIVE
Iteracja 10 — zamknięcie pętli uczenia

Finalna architektura:

                    Contextual ingestion
                           ↓
                        Memory
                    ↙      ↓      ↘
                  FTS    Vector   Graph
                           ↓
                      Candidate Set
                           ↓
                         Fusion
                           ↓
                        Reranker
                           ↓
                    Evidence Package
                           ↓
                  Sufficiency Gate
                    ↙           ↘
                   OK            Retry
                   │               ↓
                   │          Query Rewrite
                   │               ↓
                   └────────── Retrieval
                           ↓
                         Agent
                           ↓
                       RAE-Quality
                           ↓
                         Result
                           ↓
                        RAE-Lab
                           ↓
                      optimization
Jak prowadzić każdą iterację

Każda z tych iteracji powinna przechodzić identyczny cykl:

1. Specification
        ↓
2. Implementation behind feature flag
        ↓
3. Unit tests
        ↓
4. Mutation tests dla logiki krytycznej
        ↓
5. Golden retrieval benchmark
        ↓
6. Shadow mode
        ↓
7. Compare against baseline
        ↓
8. Canary
        ↓
9. Production
        ↓
10. następna iteracja

To jest dla mnie ważniejsze niż konkretna liczba etapów.

Warunek przejścia

Nigdy nie przechodzimy do kolejnej iteracji tylko dlatego, że poprzednia jest „zakodowana”.

Musi istnieć:

measured improvement

albo konkretne uzasadnienie:

same quality
but lower latency/cost
Co zleciłbym Antigravity jako pierwsze

Nie dawałbym mu całego planu jako jednego zadania implementacyjnego.

Pierwszy pakiet powinien obejmować wyłącznie Iterację 0 + Iterację 1:

ITERATION 0
Retrieval Benchmark Framework

ITERATION 1
ContextEnvelope + Contextual Ingestion

I zatrzymać się.

Po pomiarze:

baseline
vs
ContextEnvelope

decydujemy o Iteracji 2.

To jest szczególnie ważne, bo HybridSearchEngine jest już rozbudowany: ma parallel strategies, fusion, reranking, graph_store, cache i dodatkową logikę. Nie ma sensu wrzucać na niego pięciu nowych mechanizmów równocześnie i dopiero potem próbować ustalić, który z nich poprawił albo popsuł retrieval.

Jeżeli chcesz, następnym krokiem przygotuję gotowy prompt/specyfikację dla Antigravity dla Iteracji 0 i 1, z konkretnymi plikami do utworzenia/modyfikacji, API, testami, Definition of Done i zakazami zmian — tak aby można było go wkleić praktycznie 1:1.
