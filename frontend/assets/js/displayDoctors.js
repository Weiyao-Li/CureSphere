$(document).ready(function() {
  const doctorDataString = localStorage.getItem('doctorData');
  const cleanedDataString = doctorDataString.slice(1, -1).replace(/\\"/g, '"');
  const doctorData = JSON.parse(cleanedDataString);

  if (doctorData) {
    for (const doctor of doctorData) {
      const doctorElement = `
        <div class="doctor">
          <h3>${doctor.firstName} ${doctor.lastName}</h3>
          <p>Clinic Zip Code: ${doctor.clinic_zip_code}</p>
        </div>
      `;
      $('#doctor-container').append(doctorElement);
    }
  } else {
    $('#doctor-container').append('<p>No doctors found.</p>');
  }
});
