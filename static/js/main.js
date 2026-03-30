setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity .5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  });
}, 4000);


const zone = document.querySelector('.upload-zone');
const fileInput = document.getElementById('attachment');
if (zone && fileInput) {
  zone.addEventListener('click', () => fileInput.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault(); zone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) { zone.querySelector('p').innerHTML = <i class="fa-solid fa-file-circle-check" style="color:var(--student)"></i> ${file.name}; fileInput.files = e.dataTransfer.files; }
  });
  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) zone.querySelector('p').innerHTML = <i class="fa-solid fa-file-circle-check" style="color:var(--student)"></i> ${fileInput.files[0].name};
  });
}


const path = window.location.pathname;
document.querySelectorAll('.nav-item').forEach(item => {
  const href = item.getAttribute('href');
  if (href && path.startsWith(href)) {
    const role = document.body.dataset.role || 'student';
    item.classList.add(active-${role});
  }
});