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
