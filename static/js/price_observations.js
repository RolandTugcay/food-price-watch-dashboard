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


// document.addEventListener('DOMContentLoaded', () => {
// const checkboxes = document.querySelectorAll('.commodity-checkbox');
// const hiddenInput = document.getElementById('commodity_ids');

// // Attach an explicit change listener to every individual checkbox
// checkboxes.forEach(checkbox => {
//     checkbox.addEventListener('change', (event) => {
//         // This runs instantly the moment a specific checkbox is clicked/changed
//         console.log(`Checkbox ${event.target.value} changed to:`, event.target.checked);
        
//         updateHiddenInput();
//     });
// });

// function updateHiddenInput() {
//     const checkedValues = Array.from(checkboxes)
//                                 .filter(cb => cb.checked)
//                                 .map(cb => cb.value);
    
//     hiddenInput.value = checkedValues.join(',');
// }
// });

// function handleCheckboxChange(checkbox) {
//     const hiddenInput = document.getElementById('commodity_ids');
//     const allCheckboxes = document.querySelectorAll('.commodity-checkbox');
    
//     const checkedValues = Array.from(allCheckboxes)
//                                .filter(cb => cb.checked)
//                                .map(cb => cb.value);
                               
//     hiddenInput.value = checkedValues.join(',');
// }
