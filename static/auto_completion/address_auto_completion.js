document.addEventListener("DOMContentLoaded", function () {
  // 🔓 Decrypt from server-provided variable
  function decryptKey(encrypted) {
    try {
      return atob(encrypted); // base64 decode
    } catch {
      console.error("Failed to decrypt API key");
      return "";
    }
  }

  const apiKey = decryptKey(window.ADDRESS_API_KEY);

  function setupAutocomplete(inputId, resultsId) {
    const input = document.getElementById(inputId);
    const resultsBox = document.getElementById(resultsId);

    if (!input || !resultsBox) return;

    input.addEventListener("input", async function () {
      const query = input.value.trim();

      if (query.length < 3) {
        resultsBox.innerHTML = "";
        return;
      }

      const url = `https://api.locationiq.com/v1/autocomplete?key=${apiKey}&q=${encodeURIComponent(query)}&limit=5`;

      try {
        const response = await fetch(url);
        const results = await response.json();

        resultsBox.innerHTML = "";

        results.forEach((place) => {
          const item = document.createElement("div");
          item.className = "autocomplete-item";
          item.textContent = place.display_name;

          item.onclick = () => {
            input.value = place.display_name;
            resultsBox.innerHTML = "";
          };

          resultsBox.appendChild(item);
        });
      } catch (error) {
        console.error("Autocomplete error:", error);
        resultsBox.innerHTML = "";
      }
    });

    document.addEventListener("click", function (e) {
      if (!resultsBox.contains(e.target) && e.target !== input) {
        resultsBox.innerHTML = "";
      }
    });
  }

  // Enable for address1 → address9
  for (let i = 1; i <= 9; i++) {
    setupAutocomplete(`address${i}`, `results${i}`);
  }
});
