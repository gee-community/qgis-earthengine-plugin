document.addEventListener('DOMContentLoaded', function () {
    // Como index.html queda en la raíz del sitio, esta ruta funciona:
    const url = 'data/metric_info.json';

    fetch(url)
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then((data) => {
            // El JSON que mostraste es un array con un solo objeto
            const rec = Array.isArray(data) ? data[0] : data;
            if (!rec) return;

            const fmt = new Intl.NumberFormat(navigator.language || 'en');

            // ⭐ votos (en tu JSON se llama stars_votes)
            const ratingEl = document.getElementById('rating-value');
            if (ratingEl != null && rec.stars_votes != null) {
                ratingEl.textContent = fmt.format(rec.stars_votes);
            }

            // ⬇️ descargas
            const downloadsEl = document.getElementById('downloads-value');
            if (downloadsEl != null && rec.downloads != null) {
                downloadsEl.textContent = fmt.format(rec.downloads);
            }

            // (Opcional) última versión/fecha
            const latestEl = document.getElementById('latest-version');
            if (latestEl != null && rec.latest_version) {
                const d = new Date(rec.latest_version);
                latestEl.textContent = d.toLocaleDateString(
                    navigator.language || 'en',
                    { year: 'numeric', month: 'short', day: '2-digit' }
                );
            }
        })
        .catch((err) => console.error('Error loading JSON:', err));
});
