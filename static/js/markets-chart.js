// Record Distribution by Province
document.addEventListener("DOMContentLoaded", initializeProvincePriceMap);

async function initializeProvincePriceMap() {
    const mapElement = document.getElementById("recordDistByProv");
    const recordDataElement = document.getElementById("rec-dist-by-prov-data");
    const filesElement = document.getElementById("region-geojson-files");

    if (!mapElement || !recordDataElement || !filesElement) {
        console.error("Province map element or map data is missing.");
        return;
    }

    const baseUrl = mapElement.dataset.geojsonBaseUrl;

    if (!baseUrl) {
        console.error("The GeoJSON base URL is missing from #recordDistByProv.");
        return;
    }

    let recordRows;
    let geoJsonFiles;

    try {
        recordRows = JSON.parse(recordDataElement.textContent);
        geoJsonFiles = JSON.parse(filesElement.textContent);
    } catch (error) {
        console.error("Could not parse map data:", error);
        return;
    }

    const dataByProvince = new Map(
        recordRows.map(row => [
            normalizeName(row.province),
            {
                recordCount: Number(row.record_count),
                commodityCount: Number(row.com_count)
            }
        ])
    );
    const metropolitanManilaData = dataByProvince.get(
        normalizeName("Metropolitan Manila")
    );
    const provinceAliases = new Map([
        ["davao de oro", "compostela valley"],
        ["cotabato", "north cotabato"]
    ]);

    function getProvinceData(feature) {
        const provinceName = normalizeName(feature.properties?.adm2_en);
        const dataName = provinceAliases.get(provinceName) || provinceName;

        return dataByProvince.get(dataName);
    }

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
        const mapResizeObserver = new ResizeObserver(() => map.invalidateSize());
        mapResizeObserver.observe(mapElement);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 18
        }).addTo(map);

        const records = [...dataByProvince.values()]
            .map(data => data.recordCount)
            .filter(Number.isFinite);
        const minRecord = Math.min(...records);
        const maxRecord = Math.max(...records);

        function getColor(record) {
            if (!Number.isFinite(record)) {
                return "#d9d9d9"; // No matching record data
            }

            if (maxRecord === minRecord) {
                return "#b2182b";
            }

            const fraction = (record - minRecord) / (maxRecord - minRecord);
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
            const isMetropolitanManila = isNcrFeature(feature);
            const provinceData = isMetropolitanManila &&
                Number.isFinite(metropolitanManilaData?.recordCount)
                ? metropolitanManilaData
                : getProvinceData(feature);

            return {
                fillColor: getColor(provinceData?.recordCount),
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
            const provinceData = isMetropolitanManila &&
                Number.isFinite(metropolitanManilaData?.recordCount)
                ? metropolitanManilaData
                : getProvinceData(feature);
            const displayName = isMetropolitanManila &&
                Number.isFinite(metropolitanManilaData?.recordCount)
                ? "Metropolitan Manila (NCR)"
                : provinceName;

            layer.bindTooltip(
                Number.isFinite(provinceData?.recordCount)
                    ? `${displayName}<br>` +
                        `Price observation records: ${provinceData.recordCount.toLocaleString()}<br>` +
                        `Monitored commodities count: ${provinceData.commodityCount.toLocaleString()}`
                    : `${displayName}: no data`
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

        addLegend(map, minRecord, maxRecord, records.length > 0);
    } catch (error) {
        console.error("Could not initialize map:", error);
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

function addLegend(map, minRecord, maxRecord, hasRecords) {
    const legend = L.control({ position: "bottomright" });

    legend.onAdd = function () {
        const div = L.DomUtil.create("div", "record-map-legend");

        if (!hasRecords) {
            div.innerHTML = "<strong>No record data</strong>";
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

        let content = "<strong>Price Observation Records</strong>";

        for (let i = 0; i < colors.length; i++) {
            const start = minRecord + (maxRecord - minRecord) * (i / steps);
            const end = minRecord + (maxRecord - minRecord) * ((i + 1) / steps);

            content += `
                <div>
                    <span style="
                        display:inline-block;
                        width:14px;
                        height:14px;
                        margin-right:6px;
                        background:${colors[i]};
                    "></span>
                    ${Math.round(start).toLocaleString()}–${Math.round(end).toLocaleString()}
                </div>
            `;
        }

        div.innerHTML = content;
        return div;
    };

    legend.addTo(map);
}