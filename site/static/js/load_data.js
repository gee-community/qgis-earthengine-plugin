document.addEventListener('DOMContentLoaded', function () {
    fetch('../data/metric_info.json')  // Ajusta la ruta a tu archivo JSON
        .then(response => response.json())
        .then(data => {
            // Actualizar el rating
            const ratingElement = document.getElementById('rating-value');
            if (ratingElement && data.rating - values) {
                ratingElement.textContent = data.rating - value;
            }

            // Actualizar los downloads
            const downloadsElement = document.getElementById('downloads-value');
            if (downloadsElement && data.downloads - value) {
                downloadsElement.textContent = data.downloads - value.toLocaleString();
            }
        })
        .catch(error => console.error('Error loading JSON:', error));
});