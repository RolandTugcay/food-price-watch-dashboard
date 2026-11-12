// Commodity Price Trend Chart 
const comPriceTrendDataElement = document.getElementById("com-price-trend-data");
const comPriceTrendDataCanvas = document.getElementById("commodityPriceTrendCanvas");

if (comPriceTrendDataElement && comPriceTrendDataCanvas) {
    const comPriceTrendChart = JSON.parse(comPriceTrendDataElement.textContent);

    new Chart(comPriceTrendDataCanvas, {
        type: "line",
        data: comPriceTrendChart,
        options: {
            responsive: true,
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}


// Commodity Price Trend Chart - All Markets
const comPriceTrendAllMktDataElement = document.getElementById("com_price_trend_all_mkt_rows_chart_data");
const comPriceTrendAllMktCanvas = document.getElementById("commodityPriceTrendAllMktCanvas");

if (comPriceTrendAllMktDataElement && comPriceTrendAllMktCanvas) {
    const comPriceTrendAllMktChart = JSON.parse(comPriceTrendAllMktDataElement.textContent);

    new Chart(comPriceTrendAllMktCanvas, {
        type: "line",
        data: comPriceTrendAllMktChart,
        options: {
            responsive: true,
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}