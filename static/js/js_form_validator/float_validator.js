const inputs = [
  { input: document.getElementById('floatInput1'), message: document.getElementById('message1') },
  { input: document.getElementById('floatInput2'), message: document.getElementById('message2') },
  { input: document.getElementById('floatInput3'), message: document.getElementById('message3') },
  { input: document.getElementById('floatInput4'), message: document.getElementById('message4') }
];

const fullFloatRegex = /^-?\d+(\.\d+)?$/;

function validateInput(inputElem, messageElem) {
  const values = inputElem.value.split(',').map(v => v.trim()).filter(v => v !== "");

  if (values.length === 0) {
    inputElem.classList.remove('valid', 'invalid');
    messageElem.textContent = "";
    messageElem.classList.remove('valid', 'invalid');
    return true;
  }

  for (let val of values) {
    if (val === "-" || val === "." || val === "-.") {
      return false; // incomplete float
    } else if (!fullFloatRegex.test(val)) {
      inputElem.classList.add('invalid');
      inputElem.classList.remove('valid');
      messageElem.textContent = `❌ Invalid amount: "${val}"`;
      messageElem.classList.add('invalid');
      messageElem.classList.remove('valid');
      return false;
    }
  }

  // ✅ valid case
  inputElem.classList.add('valid');
  inputElem.classList.remove('invalid');
  messageElem.textContent = "✔ Valid amount(s)";
  messageElem.classList.add('valid');
  messageElem.classList.remove('invalid');
  return true;
}

// validate on submit
function validateForm() {
  let allValid = true;
  inputs.forEach(({ input, message }) => {
    if (!validateInput(input, message)) {
      allValid = false;
    }
  });

  if (!allValid) {
    alert("⚠ Please correct invalid freight quotes before submitting.");
    return false; // stop form submission
  }

  // alert("✅ Form submitted successfully!");
  return true; // allow submission
}

// also validate as user types (optional)
inputs.forEach(({ input, message }) => {
  input.addEventListener("input", () => validateInput(input, message));
});