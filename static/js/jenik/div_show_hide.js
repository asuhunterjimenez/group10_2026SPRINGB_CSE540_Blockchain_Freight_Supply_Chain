$(document).ready(function () {
  $('#service_type').change(function () {
    let val = $(this).val();

    // Hide all sections first
    $('#show_ocean_freight, #show_air_freight, #show_customs_brokerage, #show_roro').hide();

    // Show the selected one
    if (val === 'Ocean Freight') {
      $('#show_ocean_freight').show();
    }
    else if (val === 'Air Freight') {
      $('#show_air_freight').show();
    }
    else if (val === 'Customs Brokerage') {
      $('#show_customs_brokerage').show();
    }
    else if (val === 'RORO') {
      $('#show_roro').show();
    }
  });

  // Hide all by default
  $('#show_ocean_freight, #show_air_freight, #show_customs_brokerage, #show_roro').hide();

  // Initialize
  $('#service_type').trigger('change');
});



