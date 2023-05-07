var apigClient = apigClientFactory.newClient();

// Add event listeners for buttons
document.getElementById("loginBtn").addEventListener("click", function () {
    document.getElementById("loginForm").style.display = "block";
    document.getElementById("registerForm").style.display = "none";
});

document.getElementById("registerBtn").addEventListener("click", function () {
    document.getElementById("registerForm").style.display = "block";
    document.getElementById("loginForm").style.display = "none";
});

document.getElementById("registerDoctorBtn").addEventListener("click", function () {
    document.getElementById("doctorForm").style.display = "block";
});

document.getElementById("registerPatientBtn").addEventListener("click", function () {
    document.getElementById("patientForm").style.display = "block";
    document.getElementById("doctorForm").style.display = "none";
});

// Login function - old
// function login(username, password) {
//         var params = {
//             'username': username,
//             'password': password
//         };
//
//         var additionalParams = {
//             headers: {
//                 'Content-Type': 'application/json',
//                 'Access-Control-Allow-Headers': '*',
//                 'Access-Control-Allow-Origin': '*',
//                 'Access-Control-Allow-Methods': '*',
//             }
//         };
//
//         apigClient.loginPost(params, {}, additionalParams)
//             .then(function (result) {
//                 // Call the populateDayAndSlots function with the result data
//                 console.log('Login result: ', result['body']['result'])
//                 if (result['body']['result'] === 'patient') {
//                     window.location.href = 'patientPortal.html';
//                 } else if (result['body']['result'] === 'doctor') {
//                     window.location.href = 'doctorPortal.html';
//                 } else {
//                     alert('Invalid username or password. Please try again.');
//                 }
//             }).catch(function (result) {
//             console.log("Failed to find a doctor/patient user: ", result);
//             if (result['status'] === 400) {
//                 alert('Logging failed!')
//             }
//         });
// }

// Login function - new
// Login function
function login(username, password) {
    var params = {
        'username': username,
        'password': password
    };

    var additionalParams = {
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        }
    };

    apigClient.loginPost(params, {}, additionalParams)
        .then(function (result) {
            // Call the populateDayAndSlots function with the result data
            console.log('Login result: ', result);
            let responseBody = result.data;
            if (responseBody.result === 'patient') {
                window.location.href = 'patientPortal.html';
            } else if (responseBody.result === 'doctor') {
                window.location.href = 'doctorPortal.html';
            } else {
                alert('Invalid username or password. Please try again.');
            }
        }).catch(function (result) {
        console.log("Failed to find a doctor/patient user: ", result);
        if (result.status === 400) {
            alert('Logging failed!')
        }
    });
}



// Search for a user in the specified DynamoDB table
function searchUserInDB(username, tableName) {
    return new Promise((resolve, reject) => {
        let params;

        if (tableName === 'patients') {
            params = {
                TableName: tableName,
                Key: {
                    'patient_id': username
                }
            };
        } else if (tableName === 'doctors') {
            params = {
                TableName: tableName,
                Key: {
                    'doctor_id': username
                }
            };
        } else {
            reject(new Error('Invalid table name provided.'));
        }
        // dynamoDB.get(params, (error, data) => {
        //     if (error) {
        //         reject(error);
        //     } else {
        //         resolve(data.Item);
        //     }
        // });
    });
}


// Add event listener for the login form submission
document.getElementById("loginForm").addEventListener("submit", function (event) {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    login(username, password);
});

function createTimeOptions() {
    const hours = Array.from({ length: 12 }, (_, i) => (i === 0 ? 12 : i));
    const amPm = ['AM', 'PM'];

    return hours.flatMap((hour) =>
        amPm.map((period) => `${hour}:00 ${period}`)
    );
}

function populateTimeOptions() {
    const timeOptions = createTimeOptions();
    const startTimes = document.querySelectorAll('.startTime');
    const endTimes = document.querySelectorAll('.endTime');

    startTimes.forEach((select) => {
        timeOptions.forEach((time) => {
            const option = document.createElement('option');
            option.value = time;
            option.text = time;
            select.add(option);
        });
    });

    endTimes.forEach((select) => {
        timeOptions.slice(1).forEach((time) => {
            const option = document.createElement('option');
            option.value = time;
            option.text = time;
            select.add(option);
        });
    });
}

function enableDisableTimes(checkbox, startSelect, endSelect) {
    if (checkbox.checked) {
        startSelect.disabled = false;
        endSelect.disabled = false;
    } else {
        startSelect.disabled = true;
        endSelect.disabled = true;
    }
}

function adjustEndTimeOptions(startTimeSelect, endTimeSelect) {
    const selectedIndex = startTimeSelect.selectedIndex;
    const endTimeOptions = Array.from(endTimeSelect.options);

    endTimeOptions.forEach((option, index) => {
        option.disabled = index <= selectedIndex;
    });

    endTimeSelect.selectedIndex = selectedIndex + 1;
}

document.addEventListener('DOMContentLoaded', () => {
    populateTimeOptions();

    const daysCheckboxes = document.querySelectorAll('input[type="checkbox"][name="days"]');
    const startTimeSelects = document.querySelectorAll('.startTime');
    const endTimeSelects = document.querySelectorAll('.endTime');

    daysCheckboxes.forEach((checkbox, index) => {
        enableDisableTimes(checkbox, startTimeSelects[index], endTimeSelects[index]);

        checkbox.addEventListener('change', () => {
            enableDisableTimes(checkbox, startTimeSelects[index], endTimeSelects[index]);
        });
    });

    startTimeSelects.forEach((select, index) => {
        select.addEventListener('change', () => {
            adjustEndTimeOptions(select, endTimeSelects[index]);
        });
    });
});


function registerDoctor(event) {
    event.preventDefault();

    const formData = new FormData(event.target);

    const data = {};
    const available_days = [];
    const available_time_slots = [];

    const daysCheckboxes = document.querySelectorAll('input[type="checkbox"][name="days"]');
    const startTimeSelects = document.querySelectorAll('.startTime');
    const endTimeSelects = document.querySelectorAll('.endTime');

    daysCheckboxes.forEach((checkbox, index) => {
        if (checkbox.checked) {
            const day = checkbox.value;
            const startTime = startTimeSelects[index].value;
            const endTime = endTimeSelects[index].value;

            if (startTime && endTime) {
                const timeSlot = startTime + "-" + endTime;
                available_days.push(day);
                available_time_slots.push(timeSlot.replace(/ /g, '')); // remove spaces
            }
        }
    });

    formData.forEach((value, key) => {
        if (key !== "days") {
            data[key] = value;
        }
    });

    const formatted_available_days = '[' + available_days.join(',') + ']';
    const formatted_available_time_slots = '[' + available_time_slots.join(',') + ']';

    const params = {
        specialties: data.specialty,
        clinic_zip_code: data.doctorZipCode,
        firstName: data.doctorFirstName,
        department: data.department,
        email: data.doctorUsername,
        lastName: data.doctorLastName,
        city: data.city,
        available_days: formatted_available_days,
        available_time_slots: formatted_available_time_slots,
    };

    console.log('available_days:', formatted_available_days);
    console.log('available_time_slots:', formatted_available_time_slots);

    var additionalParams = {
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        }
    };

    apigClient.createDoctorPost(params, data, additionalParams)
        .then((result) => {
            if (result.success) {
                alert("Doctor registered successfully!");
            } else {
                alert("Failed to register doctor.");
            }
        })
        .catch((error) => {
            console.error("Error registering doctor:", error);
            alert("An error occurred while registering the doctor. Please try again.");
        });
}


document.getElementById("doctorForm").addEventListener("submit", registerDoctor);

