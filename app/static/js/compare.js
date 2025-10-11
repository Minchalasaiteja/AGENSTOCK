// Compare Stocks page logic for AGENSTOCK

document.addEventListener('DOMContentLoaded', () => {
    const compareForm = document.getElementById('compareForm');
    const symbolsInput = document.getElementById('symbolsInput');
    const metricsInput = document.getElementById('metricsInput');
    const compareResults = document.getElementById('compareResults');

    compareForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const symbols = symbolsInput.value.split(',').map(s => s.trim().toUpperCase()).filter(Boolean);
        const metrics = metricsInput.value.split(',').map(m => m.trim()).filter(Boolean);
        if (symbols.length < 2) {
            compareResults.innerHTML = '<div class="error">Please enter at least two stock symbols.</div>';
            return;
        }
        compareResults.innerHTML = '<div class="loading">Comparing stocks...</div>';
        try {
            const response = await fetch('/api/research/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ symbols, metrics })
            });
            if (response.ok) {
                const data = await response.json();
                renderComparison(data.comparison, data.symbols);
            } else {
                const error = await response.json().catch(() => ({ detail: 'Comparison failed' }));
                compareResults.innerHTML = `<div class="error">${error.detail}</div>`;
            }
        } catch (err) {
            compareResults.innerHTML = `<div class="error">${err.message}</div>`;
        }
    });

    function renderComparison(comparison, symbols) {
        if (!comparison || !Array.isArray(comparison)) {
            compareResults.innerHTML = '<div class="error">No comparison data available.</div>';
            return;
        }
        let html = `<table class="compare-table"><thead><tr><th>Metric</th>`;
        symbols.forEach(sym => { html += `<th>${sym}</th>`; });
        html += '</tr></thead><tbody>';
        comparison.forEach(row => {
            html += `<tr><td>${row.metric}</td>`;
            symbols.forEach(sym => { html += `<td>${row[sym] ?? '-'}</td>`; });
            html += '</tr>';
        });
        html += '</tbody></table>';
        compareResults.innerHTML = html;
    }
});
