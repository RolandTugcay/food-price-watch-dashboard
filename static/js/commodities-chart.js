// UNIQUE COMMODITIES PER CATEGORY
const uniqComPerCatDataElem = document.getElementById("uniq-com-per-cat-data");
const uniqComPerCatCanvas = document.getElementById("uniqComPerCatCanvas");

if (uniqComPerCatDataElem && uniqComPerCatCanvas) {
    const uniqComPerCatChart = JSON.parse(uniqComPerCatDataElem.textContent);

    new Chart(uniqComPerCatCanvas, {
        type: "bar",
        data: uniqComPerCatChart,
        options: {
            responsive: true,
            indexAxis: 'y',
            elements: {
                bar: {
                    borderWidth: 2
                }
            }
        }
    });
}


// DATA RECORDS BREAKDOWN BY CATEGORY AND PRICE_TYPE
const dataRecordsBreakdownDataElem = document.getElementById("data-records-breakdown-data");
const dataRecordsBreakdownCanvas = document.getElementById("dataRecordsBreakdownCanvas");

if (dataRecordsBreakdownDataElem && dataRecordsBreakdownCanvas) {
    const dataRecordsBreakdownChart = JSON.parse(dataRecordsBreakdownDataElem.textContent);
    
    new Chart(dataRecordsBreakdownCanvas, {
        type: "bar",
        data: dataRecordsBreakdownChart,
        options: {
            responsive: true,
            indexAxis: 'y',
            elements: {
                bar: {
                    borderWidth: 2
                }
            },
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true
                }
            }
        }
    });
}