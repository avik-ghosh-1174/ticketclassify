setTimeout(function () {
  document.querySelectorAll('.flash').forEach(function (el) {
    el.style.transition = 'opacity .5s';
    el.style.opacity = '0';
    setTimeout(function () { el.remove(); }, 500);
  });
}, 4500);


document.addEventListener('DOMContentLoaded', function () {
  var zone      = document.querySelector('.upload-zone');
  var fileInput = document.getElementById('attachment');
  var fileLabel = document.getElementById('file-label');

  if (zone && fileInput) {
    
    zone.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      fileInput.click();
    });

    zone.addEventListener('dragover', function (e) {
      e.preventDefault();
      zone.classList.add('dragover');
    });
    zone.addEventListener('dragleave', function () {
      zone.classList.remove('dragover');
    });
    zone.addEventListener('drop', function (e) {
      e.preventDefault();
      zone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        
        try {
          var dt = new DataTransfer();
          dt.items.add(e.dataTransfer.files[0]);
          fileInput.files = dt.files;
        } catch(err) { /* fallback for older browsers */ }
        updateLabel(e.dataTransfer.files[0].name);
      }
    });

    fileInput.addEventListener('change', function () {
      if (fileInput.files && fileInput.files.length > 0) {
        updateLabel(fileInput.files[0].name);
      }
    });

    function updateLabel(name) {
      if (fileLabel) {
        fileLabel.innerHTML = '<i class="fa-solid fa-file-circle-check"></i> ' + name;
        fileLabel.style.color = '#15803d';
        fileLabel.style.fontWeight = '600';
      }
    }
  }

  
  var path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(function (item) {
    var href = item.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) {
      item.classList.add('active');
    }
  });
});
