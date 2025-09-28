$(function() {
  // Dark mode toggle
  const theme = localStorage.getItem('theme') || 'light';
  if (theme === 'dark') {
    $('body').addClass('dark-mode');
    $('#themeToggle').prop('checked', true);
  }
  $('#themeToggle').on('change', function() {
    if ($(this).is(':checked')) {
      $('body').addClass('dark-mode');
      localStorage.setItem('theme', 'dark');
    } else {
      $('body').removeClass('dark-mode');
      localStorage.setItem('theme', 'light');
    }
  });

  // Complaint form validation
  $('#complaintForm').on('submit', function(e) {
    const dept = $('#department').val() || '';
    const region = $('#region').val() || '';
    const desc = $('textarea[name="description"]').val() || '';
    if (!dept || !region || desc.trim().length < 10) {
      e.preventDefault();
      $('#errorMsg').text('Please select department, region, and write at least 10 characters.').show();
      setTimeout(()=> $('#errorMsg').fadeOut(), 4000);
      return false;
    }
  });
});
