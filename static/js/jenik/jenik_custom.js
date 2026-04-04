// for text area character count and date picker functionality
function updateCounter() {
  const textarea = document.getElementById('jenik_text_area_id');
  const counter = document.getElementById('charCount');
  const length = textarea.value.length;
  counter.textContent = `${length} / 300`;
}






