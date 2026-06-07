/*
 * LP Gestion Atelier — amélioration mobile des champs photo.
 *
 * Objectif : éviter le comportement aléatoire de certains navigateurs mobiles
 * qui n'ouvrent que la galerie ou qui ignorent l'attribut HTML `capture`.
 *
 * Principe retenu :
 *   1. conserver le champ fichier d'origine pour la galerie ;
 *   2. créer un second champ fichier, désactivé par défaut, dédié caméra ;
 *   3. n'activer qu'un seul des deux champs avant soumission du formulaire ;
 *   4. afficher deux boutons explicites : "Prendre une photo" et
 *      "Choisir une photo".
 *
 * Cette logique est volontairement écrite en JavaScript natif pour rester
 * compatible avec tous les modules Django de la suite sans dépendance externe.
 */
(function () {
  'use strict';

  function hasCameraMarker(input) {
    return input && (
      input.dataset.cameraUpload === '1' ||
      input.dataset.cameraUploadConditional ||
      input.dataset.cameraSelectName
    );
  }

  function isImageNamedField(input) {
    var accept = (input.getAttribute('accept') || '').toLowerCase();
    var name = (input.getAttribute('name') || '').toLowerCase();
    var id = (input.getAttribute('id') || '').toLowerCase();
    return accept.indexOf('image') !== -1 || /(^|_)(photo|image|picture)(_|$)/.test(name) || /(^|_)(photo|image|picture)(_|$)/.test(id);
  }

  function isConditionalActive(input) {
    var expected = input.dataset.cameraUploadConditional;
    var selectName = input.dataset.cameraSelectName;
    if (!expected || !selectName || !input.form) return true;
    var selector = '[name="' + String(selectName).replace(/"/g, '\\"') + '"]';
    var select = input.form.querySelector(selector);
    return !select || select.value === expected;
  }

  function isEnhanceableInput(input) {
    if (!input || input.type !== 'file' || input.dataset.cameraEnhanced === '1') return false;
    if (hasCameraMarker(input)) return true;
    return isImageNamedField(input);
  }

  function makeButton(text, modifier) {
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'camera-upload-btn ' + modifier;
    button.textContent = text;
    return button;
  }

  function filenameFromInput(input) {
    if (!input || !input.files || !input.files.length) return '';
    return input.files[0].name || 'image sélectionnée';
  }

  function updatePreview(preview, input, status) {
    var file = input && input.files && input.files[0] ? input.files[0] : null;
    if (!file) {
      preview.textContent = status || 'Aucune image sélectionnée.';
      preview.classList.remove('has-preview');
      preview.style.backgroundImage = '';
      return;
    }
    preview.textContent = filenameFromInput(input);
    preview.classList.add('has-preview');
    if (file.type && file.type.indexOf('image/') === 0 && window.URL && URL.createObjectURL) {
      var previous = preview.dataset.objectUrl;
      if (previous) URL.revokeObjectURL(previous);
      var url = URL.createObjectURL(file);
      preview.dataset.objectUrl = url;
      preview.style.backgroundImage = 'url("' + url + '")';
    }
  }

  function setImageMode(input, cameraInput, enabled) {
    input.setAttribute('accept', enabled ? 'image/*' : (input.dataset.originalAccept || ''));
    cameraInput.disabled = true;
    input.disabled = false;
  }

  function enhance(input) {
    if (!isEnhanceableInput(input)) return;

    input.dataset.cameraEnhanced = '1';
    input.dataset.originalAccept = input.getAttribute('accept') || '';
    input.setAttribute('accept', 'image/*');
    input.classList.add('camera-upload-native', 'camera-upload-gallery-input');
    input.removeAttribute('capture');

    var wrapper = document.createElement('div');
    wrapper.className = 'camera-upload-widget';
    wrapper.dataset.fieldName = input.getAttribute('name') || '';

    var actions = document.createElement('div');
    actions.className = 'camera-upload-actions';

    var cameraButton = makeButton('Prendre une photo', 'primary');
    var galleryButton = makeButton('Choisir une photo', 'secondary');
    var resetButton = makeButton('Effacer sélection', 'ghost');

    var preview = document.createElement('div');
    preview.className = 'camera-upload-preview';
    preview.setAttribute('aria-live', 'polite');
    preview.textContent = 'Aucune image sélectionnée.';

    var help = document.createElement('div');
    help.className = 'camera-upload-help';
    help.textContent = 'Compatibilité mobile : utiliser “Prendre une photo” pour ouvrir la caméra, ou “Choisir une photo” pour la galerie.';

    var cameraInput = input.cloneNode(false);
    cameraInput.value = '';
    cameraInput.dataset.cameraEnhanced = '1';
    cameraInput.classList.add('camera-upload-native', 'camera-upload-camera-input');
    cameraInput.classList.remove('camera-upload-gallery-input');
    cameraInput.setAttribute('accept', 'image/*');
    cameraInput.setAttribute('capture', 'environment');
    cameraInput.disabled = true;
    if (cameraInput.id) cameraInput.id = cameraInput.id + '_camera';

    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    wrapper.appendChild(cameraInput);
    wrapper.appendChild(actions);
    actions.appendChild(cameraButton);
    actions.appendChild(galleryButton);
    actions.appendChild(resetButton);
    wrapper.appendChild(preview);
    wrapper.appendChild(help);

    galleryButton.addEventListener('click', function () {
      cameraInput.disabled = true;
      input.disabled = false;
      input.click();
    });

    cameraButton.addEventListener('click', function () {
      input.disabled = true;
      cameraInput.disabled = false;
      cameraInput.click();
    });

    resetButton.addEventListener('click', function () {
      input.disabled = false;
      cameraInput.disabled = true;
      try { input.value = ''; cameraInput.value = ''; } catch (e) {}
      updatePreview(preview, null);
    });

    input.addEventListener('change', function () {
      if (input.files && input.files.length) {
        cameraInput.disabled = true;
        input.disabled = false;
        updatePreview(preview, input);
      }
    });

    cameraInput.addEventListener('change', function () {
      if (cameraInput.files && cameraInput.files.length) {
        input.disabled = true;
        cameraInput.disabled = false;
        updatePreview(preview, cameraInput);
      }
    });

    if (input.dataset.cameraUploadConditional && input.dataset.cameraSelectName && input.form) {
      var select = input.form.querySelector('[name="' + input.dataset.cameraSelectName + '"]');
      if (select) {
        select.addEventListener('change', function () {
          setImageMode(input, cameraInput, select.value === input.dataset.cameraUploadConditional);
        });
      }
    }
  }

  function enhanceAll(root) {
    (root || document).querySelectorAll('input[type="file"]').forEach(function (input) {
      if (isConditionalActive(input)) enhance(input);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    enhanceAll(document);
    document.addEventListener('change', function (event) {
      var element = event.target;
      if (element && element.name) enhanceAll(document);
    });
  });

  window.LPCameraUploadEnhance = enhanceAll;
})();
