// =====================
//  SIGMELLE — main.js
// =====================

// Email forma
function handleSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('emailInput');
  const msg = document.getElementById('successMsg');
  const btn = e.target.querySelector('.email-btn');

  if (!input.value) return;

  // Tugmani o'chirish
  btn.textContent = '...';
  btn.disabled = true;

  // Formspree yoki EmailJS bilan ulash mumkin
  // Hozir local demo
  setTimeout(() => {
    input.style.display = 'none';
    btn.style.display = 'none';
    msg.style.display = 'block';

    // LocalStorage ga saqlash (demo uchun)
    const emails = JSON.parse(localStorage.getItem('sigmelle_emails') || '[]');
    emails.push({ email: input.value, date: new Date().toISOString() });
    localStorage.setItem('sigmelle_emails', JSON.stringify(emails));
  }, 800);
}

// Smooth scroll nav linklari uchun
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// Nav aktiv holat
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-link');

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => {
    const top = section.offsetTop - 100;
    if (window.scrollY >= top) current = section.id;
  });
  navLinks.forEach(link => {
    link.style.color = link.getAttribute('href') === '#' + current ? '#fff' : '';
  });
});
