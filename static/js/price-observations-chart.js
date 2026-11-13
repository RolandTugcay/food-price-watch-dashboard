function formatPeso(value) {
    const amount = Number(value);
    return Number.isFinite(amount)
        ? `\u20B1${amount.toLocaleString("en-PH", { maximumFractionDigits: 2 })}`
        : value;
}

function renderPriceTrendChart(dataElement, canvas, emptyMessage) {
    if (!dataElement || !canvas) {
        return;
    }

    const chartData = JSON.parse(dataElement.textContent);

    if (chartData.datasets.some(dataset => dataset.data.length > 0)) {
        new Chart(canvas, {
            type: "line",
            data: chartData,
            options: {
                responsive: true,
                tension: 0.3,
                spanGaps: true,
                scales: {
                    x: {
                        beginAtZero: true
                    },
                    y: {
                        beginAtZero: false,
                        ticks: { callback: formatPeso }
                    }
                }
            }
        });
        if (emptyMessage) {
            emptyMessage.hidden = true;
        }
    } else if (emptyMessage && document.getElementById("selected-observation").value) {
        emptyMessage.textContent = "No price trend data is available for this observation.";
    }
}

// Commodity Price Trend Chart
const comPriceTrendDataElement = document.getElementById("com-price-trend-data");
const comPriceTrendDataCanvas = document.getElementById("commodityPriceTrendCanvas");
const comPriceTrendEmptyMessage = document.getElementById("commodity-price-trend-empty");
renderPriceTrendChart(
    comPriceTrendDataElement,
    comPriceTrendDataCanvas,
    comPriceTrendEmptyMessage
);

const comPriceTrendAllMktDataElement = document.getElementById("com-price-trend-all-mkt-data");
const comPriceTrendAllMktCanvas = document.getElementById("commodityPriceTrendAllMktCanvas");
const comPriceTrendAllMktEmptyMessage = document.getElementById("commodity-price-trend-all-mkt-empty");
renderPriceTrendChart(
    comPriceTrendAllMktDataElement,
    comPriceTrendAllMktCanvas,
    comPriceTrendAllMktEmptyMessage
);