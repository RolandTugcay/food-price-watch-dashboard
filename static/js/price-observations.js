const searchInput = document.getElementById("price-obs-search");
const searchForm = document.getElementById("price-obs-search-form");
let searchTimer;

searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    document.getElementById("price-obs-page").value = "1";
    selectedObservationInput.value = "";
    searchTimer = setTimeout(() => searchForm.requestSubmit(), 350);
});

const selectedObservationInput = document.getElementById("selected-observation");

document.querySelectorAll(".commodity-checkbox").forEach(radio => {
    radio.addEventListener("change", () => {
        if (!radio.checked) return;

        selectedObservationInput.value = JSON.stringify({
            price_id: radio.dataset.priceId,
            commodity_id: radio.dataset.commodityId,
            commodity_name: radio.dataset.commodityName,
            market_name: radio.dataset.marketName,
            icon_name: radio.dataset.iconName,
            date: radio.dataset.date
        });
        searchForm.requestSubmit();
    });
});

const comPriceTrendDataElement = document.getElementById("com-price-trend-data");
const comPriceTrendCanvas = document.getElementById("commodityPriceTrendCanvas");
const comPriceTrendEmptyMessage = document.getElementById("commodity-price-trend-empty");

if (comPriceTrendDataElement && comPriceTrendCanvas) {
    const chartData = JSON.parse(comPriceTrendDataElement.textContent);

    if (chartData.datasets.some(dataset => dataset.data.length > 0)) {
        new Chart(comPriceTrendCanvas, {
            type: "line",
            data: chartData,
            options: {
                responsive: true,
                tension: 0.3,
                spanGaps: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
        if (comPriceTrendEmptyMessage) {
            comPriceTrendEmptyMessage.hidden = true;
        }
    } else if (comPriceTrendEmptyMessage && selectedObservationInput.value) {
        comPriceTrendEmptyMessage.textContent =
            "No price trend data is available for this observation.";
    }
}

const comPriceTrendAllMktDataElement = document.getElementById("com-price-trend-all-mkt-data");
const comPriceTrendAllMktCanvas = document.getElementById("commodityPriceTrendAllMktCanvas");
const comPriceTrendAllMktEmptyMessage = document.getElementById("commodity-price-trend-all-mkt-empty");

if (comPriceTrendAllMktDataElement && comPriceTrendAllMktCanvas) {
    const chartData = JSON.parse(comPriceTrendAllMktDataElement.textContent);

    if (chartData.datasets.some(dataset => dataset.data.length > 0)) {
        new Chart(comPriceTrendAllMktCanvas, {
            type: "line",
            data: chartData,
            options: {
                responsive: true,
                tension: 0.3,
                spanGaps: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
        if (comPriceTrendAllMktEmptyMessage) {
            comPriceTrendAllMktEmptyMessage.hidden = true;
        }
    } else if (comPriceTrendAllMktEmptyMessage && selectedObservationInput.value) {
        comPriceTrendAllMktEmptyMessage.textContent =
            "No price trend data is available for this observation.";
    }
}