// V1: compatible douchette USB car elle écrit simplement dans le champ sélectionné.
// Pour caméra QR code, on pourra ajouter html5-qrcode ensuite.
console.log('ToolMag ready');

// Ouverture casier : appel POST asynchrone vers ToolMag, sans URL de contrôleur exposée côté navigateur.
document.addEventListener('submit', async function(event) {
  const form = event.target;
  if (!form.classList.contains('locker-open-form')) return;
  event.preventDefault();
  const button = form.querySelector('button[type="submit"]');
  if (button) { button.disabled = true; button.textContent = 'Ouverture en cours...'; }
  try {
    const response = await fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: {'Accept': 'application/json'}
    });
    const data = await response.json();
    alert(data.message || (data.ok ? 'Casier ouvert.' : 'Ouverture refusée ou échouée.'));
  } catch (e) {
    alert('Erreur réseau pendant la demande d’ouverture casier.');
  } finally {
    if (button) { button.disabled = false; button.textContent = 'Ouvrir le casier'; }
  }
});
