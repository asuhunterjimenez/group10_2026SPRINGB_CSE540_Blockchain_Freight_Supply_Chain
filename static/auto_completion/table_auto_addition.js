// function addVehicleRow() {
//   const table = document.getElementById("vehicleTable").getElementsByTagName("tbody")[0];
//   const row = table.insertRow();
//   const fields = ['vehicle_year[]', 'vehicle_make[]', 'vehicle_vin[]', 'vehicle_cost[]', 'vehicle_color[]'];

//   fields.forEach(field => {
//     const cell = row.insertCell();
//     const input = document.createElement('input');
//     input.name = field;
//     input.required = true;
//     cell.appendChild(input);
//   });

//   const actionCell = row.insertCell();
//   const delBtn = document.createElement('button');
//   delBtn.textContent = "Delete";
//   delBtn.onclick = () => row.remove();
//   actionCell.appendChild(delBtn);
// }

// function addGoodsRow() {
//   const table = document.getElementById("goodsTable").getElementsByTagName("tbody")[0];
//   const row = table.insertRow();

//   // Add the "No." cell first
//   const noCell = row.insertCell();
//   noCell.textContent = table.rows.length;

//   const fields = ['goods_qty[]', 'goods_description[]', 'goods_value[]'];
//   fields.forEach(field => {
//     const cell = row.insertCell();
//     const input = document.createElement('input');
//     input.name = field;
//     input.required = true;
//     cell.appendChild(input);
//   });

//   const actionCell = row.insertCell();
//   const delBtn = document.createElement('button');
//   delBtn.textContent = "Delete";
//   delBtn.onclick = () => row.remove();
//   actionCell.appendChild(delBtn);
// }


// function validateRow(row, type = 'vehicle') {
//   let isValid = true;
//   const inputs = row.querySelectorAll('input');

//   inputs.forEach(input => {
//     input.classList.remove('invalid');
//     const value = input.value.trim();

//     if (input.name === 'year' && (!/^\d{4}$/.test(value))) {
//       isValid = false;
//       input.classList.add('invalid');
//     } else if (input.name === 'vin' && value.length !== 17) {
//       isValid = false;
//       input.classList.add('invalid');
//     } else if ((input.name === 'cost' || input.name === 'value') && isNaN(parseFloat(value))) {
//       isValid = false;
//       input.classList.add('invalid');
//     } else if ((input.name === 'qty' || input.name === 'no') && (!/^\d+$/.test(value))) {
//       isValid = false;
//       input.classList.add('invalid');
//     } else if (!value) {
//       isValid = false;
//       input.classList.add('invalid');
//     }
//   });

//   return isValid;
// }

// function collectDataFromTable(tableId, type) {
//   const rows = document.querySelectorAll(`#${tableId} tbody tr`);
//   const data = [];
//   let allValid = true;

//   rows.forEach(row => {
//     const isValid = validateRow(row, type);
//     if (!isValid) allValid = false;

//     const item = {};
//     row.querySelectorAll('input').forEach(input => {
//       item[input.name] = input.value.trim();
//     });
//     data.push(item);
//   });

//   return { data, allValid };
// }

// function submitData() {
//   const vehicleResult = collectDataFromTable("vehicleTable", "vehicle");
//   const goodsResult = collectDataFromTable("goodsTable", "goods");

//   if (!vehicleResult.allValid || !goodsResult.allValid) {
//     alert("Please correct invalid inputs before submitting.");
//     return;
//   }

//   // Replace below with AJAX/Fetch POST request to your backend
//   console.log("Vehicle Data:", vehicleResult.data);
//   console.log("Goods Data:", goodsResult.data);

//   alert("Data is valid and ready to send to the server!");

//   // Example: send data to your backend API

//   fetch('/submit-data/', {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json',
//       'X-CSRFToken': getCookie('csrftoken') // Django only
//     },
//     body: JSON.stringify({
//       vehicles: vehicleResult.data,
//       goods: goodsResult.data
//     })
//   }).then(response => {
//     if (response.ok) {
//       alert("Data saved successfully!");
//     }
//   });

// }