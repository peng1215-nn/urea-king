
// ── contact modal ──
const overlay = document.getElementById('modal-overlay');
function openModal()  { overlay.classList.add('open'); }
function closeModal() { overlay.classList.remove('open'); }

document.getElementById('contact-btn').addEventListener('click', openModal);
document.getElementById('modal-close').addEventListener('click', closeModal);
overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

document.getElementById('btn-copy-tpl').addEventListener('click', () => {
  const tplText = "Subject: [Issue] Your Username\n\nUsername: your username\nIssue: describe your problem here";
  const btn = document.getElementById('btn-copy-tpl');
  navigator.clipboard.writeText(tplText).then(() => {
    btn.textContent = 'Copied';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1800);
  }).catch(() => {});
});

document.getElementById('btn-copy').addEventListener('click', () => {
  const email = document.getElementById('admin-email').textContent;
  const btn = document.getElementById('btn-copy');
  navigator.clipboard.writeText(email).then(() => {
    btn.textContent = 'Copied';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1800);
  }).catch(() => {
    // fallback: select the text
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(document.getElementById('admin-email'));
    sel.removeAllRanges(); sel.addRange(range);
  });
});
