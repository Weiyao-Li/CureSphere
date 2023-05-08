$(document).ready(function () {
    const medicine = localStorage.getItem("medicine");
   // const parsed_medicine = JSON.parse(medicine);
    const parsed_medicine = "BoneStrength"
    console.log("medicine : ", parsed_medicine);

    // Initialize the API Gateway SDK
    const apigClient = apigClientFactory.newClient();

    // Call the API
    getMedicineComparison(parsed_medicine, apigClient);
});

function getMedicineComparison(medicineName, apigClient) {
    const params = {};
    const additionalParams = {
        headers: {
            medicineName: medicineName,
        },
    };

    apigClient
        .getMedicineComparisonGet(params, {}, additionalParams)
        .then((response) => {
            displayMedicineData(response.data);
        })
        .catch((error) => {
            console.error(error);
        });
}

function displayMedicineData(data) {
    const tableBody = $("#medicine-table-body");
    tableBody.empty();

    data.forEach((medicine) => {
        const tableRow = $("<tr></tr>");

        tableRow.append(`<td>${medicine.seller_name}</td>`);
        tableRow.append(`<td>${medicine.medicine_name}</td>`);
        tableRow.append(`<td>${medicine.price}</td>`);
        tableRow.append(`<td>${medicine.zip_code}</td>`);

        tableBody.append(tableRow);
    });
}
