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


// Regional Price Comparison Chart
const regionalPriceComparisonDataElement = document.getElementById("regional-price-comparison-data");
const canvasRegionalPriceComparisonChart = document.getElementById("regionalPriceComparisonChart");

if (regionalPriceComparisonDataElement && canvasRegionalPriceComparisonChart) {
    const chartDataRegionalPriceComparison = JSON.parse(regionalPriceComparisonDataElement.textContent);
    const firstDataset = chartDataRegionalPriceComparison.datasets[0];

    if (firstDataset) {
        const sortedIndexes = chartDataRegionalPriceComparison.labels
            .map((_, index) => index)
            .sort((a, b) => firstDataset.data[b] - firstDataset.data[a]);

        chartDataRegionalPriceComparison.labels = sortedIndexes.map(
            index => chartDataRegionalPriceComparison.labels[index]
        );
        chartDataRegionalPriceComparison.datasets.forEach(dataset => {
            dataset.data = sortedIndexes.map(index => dataset.data[index]);
        });

        const numericPrices = firstDataset.data.map(price =>
            price == null || price === "" ? NaN : Number(price)
        );
        const validPrices = numericPrices.filter(Number.isFinite);
        const minPrice = Math.min(...validPrices);
        const maxPrice = Math.max(...validPrices);
        const lightGreen = [169, 207, 180];
        const darkGreen = [3, 140, 140];

        firstDataset.backgroundColor = numericPrices.map(price => {
            const ratio = Number.isFinite(price) && maxPrice > minPrice
                ? (price - minPrice) / (maxPrice - minPrice)
                : 0;
            const color = lightGreen.map((lightChannel, index) =>
                Math.round(lightChannel + (darkGreen[index] - lightChannel) * ratio)
            );

            return `rgb(${color.join(", ")})`;
        });
    }

    new Chart(canvasRegionalPriceComparisonChart, {
        type: "bar",
        data: chartDataRegionalPriceComparison,
        options: {
            responsive: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    position: 'bottom',
                }
            },
            elements: {
                bar: {
                    borderWidth: 2
                }
            }
        }
    });
}


// Provincial Price Comparison - map chart
document.addEventListener("DOMContentLoaded", initializeProvincePriceMap);

async function initializeProvincePriceMap() {
    const mapElement = document.getElementById("provincePriceMap");
    const priceDataElement = document.getElementById("province-price-map-data");
    const filesElement = document.getElementById("region-geojson-files");

    if (!mapElement || !priceDataElement || !filesElement) {
        console.error("Province map element or map data is missing.");
        return;
    }

    const baseUrl = mapElement.dataset.geojsonBaseUrl;

    if (!baseUrl) {
        console.error("The GeoJSON base URL is missing from #provincePriceMap.");
        return;
    }

    let priceRows;
    let geoJsonFiles;

    try {
        priceRows = JSON.parse(priceDataElement.textContent);
        geoJsonFiles = JSON.parse(filesElement.textContent);
    } catch (error) {
        console.error("Could not parse the province map data:", error);
        return;
    }

    const priceByProvince = new Map(
        priceRows.map(row => [
            normalizeName(row.province),
            Number(row.avg_price)
        ])
    );
    const metropolitanManilaPrice = priceByProvince.get(
        normalizeName("Metropolitan Manila")
    );

    try {
        const regionCollections = await Promise.all(
            geoJsonFiles.map(async fileName => {
                const response = await fetch(
                    baseUrl + encodeURIComponent(fileName)
                );

                if (!response.ok) {
                    throw new Error(
                        `Failed to load ${fileName}: HTTP ${response.status}`
                    );
                }

                return response.json();
            })
        );

        const provinceGeoJson = {
            type: "FeatureCollection",
            features: regionCollections.flatMap(collection => collection.features || [])
        };

        const map = L.map(mapElement).setView([12.8797, 121.774], 5);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 18
        }).addTo(map);

        const prices = [...priceByProvince.values()].filter(Number.isFinite);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);

        function getColor(price) {
            if (!Number.isFinite(price)) {
                return "#d9d9d9"; // No matching price data
            }

            if (maxPrice === minPrice) {
                return "#b2182b";
            }

            const fraction = (price - minPrice) / (maxPrice - minPrice);
            const colorSteps = [
                "#fff7bc",
                "#fec44f",
                "#fe9929",
                "#ec7014",
                "#cc4c02",
                "#8c2d04"
            ];

            const index = Math.min(
                Math.floor(fraction * colorSteps.length),
                colorSteps.length - 1
            );

            return colorSteps[index];
        }

        function styleProvince(feature) {
            const provinceName = normalizeName(feature.properties?.adm2_en);
            const isMetropolitanManila = isNcrFeature(feature);
            const price = isMetropolitanManila && Number.isFinite(metropolitanManilaPrice)
                ? metropolitanManilaPrice
                : priceByProvince.get(provinceName);

            return {
                fillColor: getColor(price),
                weight: isMetropolitanManila ? 0 : 1,
                opacity: 1,
                color: "#ffffff",
                dashArray: "2",
                fillOpacity: 0.8
            };
        }

        function onEachProvince(feature, layer) {
            const provinceName = feature.properties?.adm2_en || "Unknown province";
            const isMetropolitanManila = isNcrFeature(feature);
            const price = isMetropolitanManila && Number.isFinite(metropolitanManilaPrice)
                ? metropolitanManilaPrice
                : priceByProvince.get(normalizeName(provinceName));
            const displayName = isMetropolitanManila &&
                Number.isFinite(metropolitanManilaPrice)
                ? "Metropolitan Manila (NCR)"
                : provinceName;

            layer.bindTooltip(
                Number.isFinite(price)
                    ? `${displayName}: ₱${price.toFixed(2)}`
                    : `${displayName}: no price data`
            );

            layer.on({
                mouseover: event => {
                    event.target.setStyle({
                        weight: isMetropolitanManila ? 0 : 2,
                        color: "#333333",
                        fillOpacity: 0.95
                    });
                    event.target.bringToFront();
                },
                mouseout: event => {
                    geoJsonLayer.resetStyle(event.target);
                }
            });
        }

        const geoJsonLayer = L.geoJSON(provinceGeoJson, {
            style: styleProvince,
            onEachFeature: onEachProvince
        }).addTo(map);

        if (geoJsonLayer.getBounds().isValid()) {
            map.fitBounds(geoJsonLayer.getBounds());
        }

        addLegend(map, minPrice, maxPrice, prices.length > 0);
    } catch (error) {
        console.error("Could not initialize the province price map:", error);
    }
}

function isNcrFeature(feature) {
    return Number(feature.properties?.adm1_psgc) === 1300000000;
}

function normalizeName(value) {
    return String(value ?? "")
        .trim()
        .toLowerCase()
        .replace(/\s+/g, " ");
}

function addLegend(map, minPrice, maxPrice, hasPrices) {
    const legend = L.control({ position: "bottomright" });

    legend.onAdd = function () {
        const div = L.DomUtil.create("div", "price-map-legend");

        if (!hasPrices) {
            div.innerHTML = "<strong>No price data</strong>";
            return div;
        }

        const steps = 5;
        const colors = [
            "#fff7bc",
            "#fec44f",
            "#fe9929",
            "#ec7014",
            "#cc4c02",
            "#8c2d04"
        ];

        let content = "<strong>Average price</strong>";

        for (let i = 0; i < colors.length; i++) {
            const start = minPrice + (maxPrice - minPrice) * (i / steps);
            const end = minPrice + (maxPrice - minPrice) * ((i + 1) / steps);

            content += `
                <div>
                    <span style="
                        display:inline-block;
                        width:14px;
                        height:14px;
                        margin-right:6px;
                        background:${colors[i]};
                    "></span>
                    ₱${start.toFixed(2)}–₱${end.toFixed(2)}
                </div>
            `;
        }

        div.innerHTML = content;
        return div;
    };

    legend.addTo(map);
}
