// Monthly Price Trend by Category Chart
const dataElementCategoryMonthlyTrend = document.getElementById("monthly-trend-data");
const canvasCategoryMonthlyTrendChart = document.getElementById("categoryMonthlyTrendChart");

if (dataElementCategoryMonthlyTrend && canvasCategoryMonthlyTrendChart) {
    const chartDataCatMoTrend = JSON.parse(dataElementCategoryMonthlyTrend.textContent);

    new Chart(canvasCategoryMonthlyTrendChart, {
        type: "line",
        data: chartDataCatMoTrend,
        options: {
            responsive: true,
            tension: 0.5
        }
    });
}

// Highest Price Increases Chart
const priceIncreaseDataElement = document.getElementById("highest-price-increases-data");
const canvasPriceIncreaseChart = document.getElementById("highestPriceIncreasesChart");

if (priceIncreaseDataElement && canvasPriceIncreaseChart) {
    const chartDataHighestPrcInc = JSON.parse(priceIncreaseDataElement.textContent);
    const firstDataset = chartDataHighestPrcInc.datasets[0];

    if (firstDataset) {
        const sortedIndexes = chartDataHighestPrcInc.labels
            .map((_, index) => index)
            .sort((a, b) => firstDataset.data[b] - firstDataset.data[a]);

        chartDataHighestPrcInc.labels = sortedIndexes.map(
            index => chartDataHighestPrcInc.labels[index]
        );
        chartDataHighestPrcInc.datasets.forEach(dataset => {
            dataset.data = sortedIndexes.map(index => dataset.data[index]);
        });
    }

    new Chart(canvasPriceIncreaseChart, {
        type: "bar",
        data: chartDataHighestPrcInc,
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                },
            },
            elements: {
                bar: {
                    borderWidth: 2
                }
            }
        }
    });
}