const uploadArea = document.querySelector('#uploadArea');
const dropZoon = document.querySelector('#dropZoon');
const loadingText = document.querySelector('#loadingText');
const fileInput = document.querySelector('#fileInput');
const previewImage = document.querySelector('#previewImage');
const fileDetails = document.querySelector('#fileDetails');
const uploadedFile = document.querySelector('#uploadedFile');
const uploadedFileInfo = document.querySelector('#uploadedFileInfo');
const uploadedFileName = document.querySelector('.uploaded-file__name');
const uploadedFileIconText = document.querySelector('.uploaded-file__icon-text');
const uploadedFileCounter = document.querySelector('.uploaded-file__counter');
const toolTipData = document.querySelector('.upload-area__tooltip-data');
const validFileTypes = [
    "application/pdf" 
];

const imagesTypes = [
"pdf"
];
toolTipData.innerHTML = [...imagesTypes].join(', .');
const docThumbnail = document.querySelector('#docThumbnail');
const excelThumbnail = document.querySelector('#excelThumbnail');
const pdfThumbnail = document.querySelector('#pdfThumbnail');

dropZoon.addEventListener('dragover', function (event) {
  event.preventDefault();
  dropZoon.classList.add('drop-zoon--over');
});

dropZoon.addEventListener('dragleave', function (event) {
  dropZoon.classList.remove('drop-zoon--over');
});

dropZoon.addEventListener('drop', function (event) {
  event.preventDefault();
  dropZoon.classList.remove('drop-zoon--over');

  const file = event.dataTransfer.files[0];
  uploadFile(file);
});

dropZoon.addEventListener('click', function (event) {
  fileInput.click();
});

fileInput.addEventListener('change', function (event) {
  const file = event.target.files[0];
  uploadFile(file);
});

function uploadFile(file) {
  const fileReader = new FileReader();
  const fileType = file.type;
  const fileSize = file.size;

  if (fileValidate(fileType, fileSize)) {
    dropZoon.classList.add('drop-zoon--Uploaded');
    loadingText.style.display = "block";
    previewImage.style.display = 'none';
    pdfThumbnail.style.display='none';

    uploadedFile.classList.remove('uploaded-file--open');
    uploadedFileInfo.classList.remove('uploaded-file__info--active');

    fileReader.addEventListener('load', function () {
      setTimeout(function () {
        uploadArea.classList.add('upload-area--open');
        loadingText.style.display = "none";
        if (fileType.startsWith('image/')) {
            pdfThumbnail.style.display = 'none';
          previewImage.setAttribute('src', fileReader.result);
        } else if (fileType === 'application/msword' || fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
            pdfThumbnail.style.display = 'none';
        } else if (fileType === 'application/vnd.ms-excel' || fileType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || fileType === 'text/csv') {
            pdfThumbnail.style.display = 'none';
        } else if (fileType==='application/pdf'){
            pdfThumbnail.style.display = 'block';
        }

        fileDetails.classList.add('file-details--open');
        uploadedFile.classList.add('uploaded-file--open');
        uploadedFileInfo.classList.add('uploaded-file__info--active');
      }, 500);
      previewImage.setAttribute('src', fileReader.result);
      uploadedFileName.innerHTML = file.name;
      progressMove();
    });

    fileReader.readAsDataURL(file);
  }
}

document.querySelector('.close').addEventListener('click', function() {
  document.getElementById('modal').style.display = 'none';
});

// Function to open the modal
function openModal() {
  document.getElementById('modal').style.display = 'block';
}

function progressMove() {
  let counter = 0;
  setTimeout(() => {
    let counterIncrease = setInterval(() => {
      if (counter === 100) {
        clearInterval(counterIncrease);
        document.getElementById('analyzeEmotionsBtn').style.display = 'block';
      } else {
        counter = counter + 10;
        uploadedFileCounter.innerHTML = `${counter}%`;
      }
    }, 100);
  }, 600);
}

function fileTypeValidation(fileType) {
  return validFileTypes.includes(fileType);
}

function fileValidate(fileType, fileSize) {
  if (fileTypeValidation(fileType)) {
    if (fileSize <= 5000000) {
      return true;
    } else {
      alert('Please make sure your file size is 5 Megabytes or less.');
      return false;
    }
  } else {
    alert('Please make sure to upload a valid file type (PDF).');
    return false;
  }
}

const analyzeButton = document.querySelector('#analyzeEmotionsBtn');
analyzeButton.addEventListener('click', function () {
  const uploadedFileData = fileInput.files[0];

  if (!uploadedFileData) {
    alert('Please select a file before analyzing.');
    return;
  }

  const fileExtension = uploadedFileData.name.split('.').pop().toLowerCase();
  if (['pdf'].includes(fileExtension)) {
  }

  const formData = new FormData();
  formData.append('file', uploadedFileData);

  fetch('/extract-pdf-dataV1', {
    method: 'POST',
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error('Failed to analyze the file. Please try again.');
      }
      return response.json();
    })
    .then((data) => {
      console.log('API Response:', data);
      displaySentimentResult(data);
      modal.style.display = 'block';

    })
    .catch((error) => {
      console.log('Error:', error.message);
    });
});

function displaySentimentResult(data) {
  // Assuming 'data' is a JSON string, parse it into an array of objects
  try {
    data = JSON.parse(data);
  } catch (error) {
    console.error('Error parsing API response:', error);
    return;
  }

  const tableContainer = document.getElementById('tableContainer');

  // Clear any existing content in the table container
  tableContainer.innerHTML = '';

  if (data && Array.isArray(data) && data.length > 0) {
    // Create a table element
    const table = document.createElement('table');
    table.className = 'sentiment-table';

    // Create a table header row
    const headerRow = document.createElement('tr');

    // Extract the keys from the first data item to create column headers
    const columns = Object.keys(data[0]);

    // Add table headers based on the keys
    columns.forEach((column) => {
      const th = document.createElement('th');
      th.textContent = column;
      headerRow.appendChild(th);
    });

    // Append the header row to the table
    table.appendChild(headerRow);

    // Create table rows and cells for each data item
    data.forEach((item) => {
      // Check if any data value in the row is null or empty
      if (columns.every((column) => !item[column])) {
        // Skip this row if all data values are null or empty
        return;
      }

      const row = document.createElement('tr');

      // Add table cells based on the keys
      columns.forEach((column) => {
        const cell = document.createElement('td');
        cell.textContent = item[column];
        row.appendChild(cell);
      });

      // Append the row to the table
      table.appendChild(row);
    });

    // Append the table to the table container
    tableContainer.appendChild(table);
  } else {
    // If there is no data, display a message
    tableContainer.textContent = 'No data available.';
  }
}


const downloadButton = document.querySelector('.download');
downloadButton.addEventListener('click', function () {
  const table = document.querySelector('#tableContainer table');
  const rows = table.querySelectorAll('tr');

  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.table_to_sheet(table);

  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');

  const excelFile = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
  const blob = new Blob([excelFile], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

  const downloadLink = document.createElement('a');
  downloadLink.href = URL.createObjectURL(blob);
  downloadLink.download = 'FinalExtracted.xlsx';
  downloadLink.click();
});
