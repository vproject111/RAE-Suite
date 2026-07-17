#!/bin/bash
# scripts/run_mutmut.sh
# Runs mutation testing with mutmut and checks if mutation score >= 70%

if ! command -v mutmut &> /dev/null; then
    echo "⚠️  mutmut is not installed. Skipping mutation testing."
    exit 0
fi

echo "🧬 Running mutation tests on packages/rae-quality/main.py..."
mutmut run --paths-to-mutate=packages/rae-quality/main.py > mutmut.log 2>&1

# Generate results
mutmut show all > mutmut_results.txt 2>/dev/null
killed=$(grep -c "status=killed" mutmut_results.txt || echo 0)
total=$(grep -c "status=" mutmut_results.txt || echo 0)

if [ "$total" -gt 0 ]; then
    score=$(echo "scale=2; ($killed / $total) * 100" | bc)
    echo "🧬 Mutation Score: $score% ($killed killed of $total total mutants)"
    if (( $(echo "$score < 70.0" | bc -l) )); then
        echo "❌ Mutation score $score% is below required 70% threshold!"
        exit 1
    fi
else
    echo "🧬 No mutants generated."
fi
exit 0
