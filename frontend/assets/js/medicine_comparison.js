$(document).ready(function() {
    const medicine = localStorage.getItem('medicine');
    const parsed_medicine = JSON.parse(medicine);
    console.log("medicine : ", parsed_medicine);

    displayMedicineData(parsed_medicine);
});

function displayMedicineData(data) {
    const tableBody = $("#medicine-table-body");
    tableBody.empty();

    data.forEach(medicine => {
        const tableRow = $("<tr></tr>");

        tableRow.append(`<td>${medicine.seller_name}</td>`);
        tableRow.append(`<td>${medicine.medicine_name}</td>`);
        tableRow.append(`<td>${medicine.price}</td>`);
        tableRow.append(`<td>${medicine.zip_code}</td>`);

        tableBody.append(tableRow);
    });
}
