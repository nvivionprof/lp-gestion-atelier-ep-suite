// ToolMag Bêta V1.8 — traduction légère côté interface.
// Objectif : premier niveau bilingue FR/EN sans traduire les données saisies en base.
(function(){
  const lang = (document.documentElement.getAttribute('data-toolmag-lang') || window.TOOLMAG_LANG || 'fr').slice(0,2);
  if (lang !== 'en') return;
  const dict = {
    'ToolMag': 'ToolMag',
    'Tableau de bord': 'Dashboard',
    'Inventaire': 'Inventory',
    'Utilisateurs': 'Users',
    'Affichage dynamique': 'Dynamic display',
    'Évaluation': 'Assessment',
    'Droits matériel': 'Equipment rights',
    'Terminaux': 'Devices',
    'Forçage casier': 'Locker override',
    'Sauvegardes': 'Backups',
    'Admin': 'Admin',
    'Connexion utilisateur': 'User login',
    'Connexion magasinier': 'Storekeeper login',
    'Version installée :': 'Installed version:',
    'Glossaire DNL': 'DNL glossary',

    'Disponibles': 'Available',
    'Sortis': 'Checked out',
    'En retard': 'Overdue',
    'Maintenance': 'Maintenance',
    'Incomplets': 'Incomplete',
    'Matériel actuellement sorti': 'Currently checked-out equipment',
    'Les lignes rouges signalent un matériel composé sorti dont l’inventaire utilisateur de sortie reste à faire : vérification magasinier nécessaire.': 'Red rows indicate checked-out kit equipment whose user checkout inventory is still pending: storekeeper verification required.',
    'Code': 'Code',
    'Matériel': 'Equipment',
    'Utilisateur': 'User',
    'Inv. sortie': 'Checkout inv.',
    'Inv. retour': 'Return inv.',
    'Retour prévu': 'Expected return',
    'Aucune sortie en cours.': 'No current checkout.',
    'Top utilisation': 'Top usage',
    'Sorties': 'Checkouts',
    'Nouvelle sortie': 'New checkout',
    'Retour matériel': 'Return equipment',

    'Créer un matériel': 'Create equipment',
    'Tous statuts': 'All statuses',
    'Filtrer': 'Filter',
    'Photo': 'Picture',
    'Nom': 'Name',
    'Descriptif': 'Description',
    'Type': 'Type',
    'Catégorie': 'Category',
    'Statut': 'Status',
    'État': 'Condition',
    'Lieu': 'Location',
    'Aucun matériel.': 'No equipment.',
    'Créer la séance': 'Create session',
    'Enregistrer': 'Save',
    'Annuler': 'Cancel',
    'Ajouter': 'Add',
    'Modifier': 'Edit',
    'Supprimer': 'Delete',
    'Retour fiche': 'Back to equipment page',
    'Documents': 'Documents',
    'Composants': 'Components',

    'Type :': 'Type:',
    'Statut :': 'Status:',
    'État actuel :': 'Current condition:',
    'Marque / modèle :': 'Brand / model:',
    'N° série :': 'Serial number:',
    'Emplacement :': 'Location:',
    'Descriptif matériel :': 'Equipment description:',
    'QR payload :': 'QR payload:',
    'Matériel sensible': 'Sensitive equipment',
    'Armoire sécurisée': 'Secure cabinet',
    'Armoire :': 'Cabinet:',
    'Casier :': 'Locker:',
    'Ouvrir le casier': 'Open locker',
    'Ouverture autorisée : magasinier connecté, terminal autorisé et IP conforme.': 'Opening allowed: storekeeper logged in, authorized device and compliant IP.',
    'Contrôler': 'Check',
    'Modifier la fiche': 'Edit equipment page',
    'Bon d’intervention': 'Service report',
    'Réparation / dépannage': 'Repair / troubleshooting',
    'Sortir': 'Check out',
    'Retourner': 'Return',

    'Composants attendus': 'Expected components',
    'Composant': 'Component',
    'Présent': 'Present',
    'Qté': 'Qty',
    'Oui': 'Yes',
    'Non': 'No',
    'Sans photo': 'No picture',
    'Quantité :': 'Quantity:',
    'Présent :': 'Present:',

    'Documents du matériel': 'Equipment documents',
    'Notices, fiches de prise en main, consignes de sécurité ou documents de maintenance associés à ce matériel.': 'Manuals, getting started guides, safety instructions or maintenance documents linked to this equipment.',
    'Titre': 'Title',
    'Description': 'Description',
    'Fichier': 'File',
    'Ouvrir / télécharger': 'Open / download',
    'Aucun document.': 'No document.',

    'Connexion utilisateur / emprunteur': 'User / borrower login',
    'Connexion magasinier': 'Storekeeper login',
    'Se connecter comme utilisateur': 'Log in as user',
    'Se connecter comme magasinier': 'Log in as storekeeper',
    'code': 'code',
    'mot de passe': 'password',
    'Recherche emprunteur': 'Borrower search',
    'Aucun utilisateur trouvé.': 'No user found.',
    'Aucun magasinier trouvé.': 'No storekeeper found.',
    'Recherche indisponible.': 'Search unavailable.',

    'Sortie de matériel': 'Equipment checkout',
    'Retour de matériel': 'Equipment return',
    'Magasinier connecté :': 'Logged-in storekeeper:',
    'Emprunteur connecté :': 'Logged-in borrower:',
    'Utilisateur connecté :': 'Logged-in user:',
    'Inventaire de sortie': 'Checkout inventory',
    'Inventaire de retour': 'Return inventory',
    'Valider la sortie': 'Confirm checkout',
    'Valider le retour': 'Confirm return',
    'Inventaire utilisateur de sortie reçu.': 'User checkout inventory received.',
    'Inventaire utilisateur de retour reçu.': 'User return inventory received.',
    'Le formulaire ci-dessous est prérempli ; le magasinier relit puis valide la sortie.': 'The form below is prefilled; the storekeeper reviews and confirms checkout.',
    'Le formulaire ci-dessous est prérempli ; le magasinier relit puis valide le retour.': 'The form below is prefilled; the storekeeper reviews and confirms return.',

    'Inventaire utilisateur vierge : aucune case n’est précochée. Coche chaque composant réellement présent, puis ajoute un commentaire si un élément manque ou paraît abîmé.': 'Blank user inventory: no box is pre-checked. Tick each component that is actually present, then add a comment if an item is missing or appears damaged.',
    'État des inventaires utilisateur': 'User inventory status',
    'Inventaire utilisateur de sortie :': 'User checkout inventory:',
    'Inventaire utilisateur de retour :': 'User return inventory:',
    'fait': 'done',
    'à faire': 'to do',
    'non fait': 'not done',
    'Composants contrôlés par l\'utilisateur': 'Components checked by the user',
    'Soumettre l\'inventaire au magasinier': 'Submit inventory to storekeeper',

    'Utilisateurs existants': 'Existing users',
    'Créer un utilisateur': 'Create user',
    'Télécharger le modèle Excel': 'Download Excel template',
    'Exporter les utilisateurs': 'Export users',
    'Importer / modifier par Excel': 'Import / edit with Excel',
    'Montée de niveau / archivage': 'Promotion / archiving',
    'Réinitialiser un mot de passe': 'Reset a password',
    'Identifiant': 'Username',
    'Formation': 'Training programme',
    'Classe': 'Class',
    'Groupe': 'Group',
    'Rôle': 'Role',
    'Actif': 'Active',
    'Archivé': 'Archived',
    'Action': 'Action',
    'Voir fiche': 'View profile',

    'Code :': 'Code:',
    'Identifiant :': 'Username:',
    'Formation :': 'Training programme:',
    'Classe / groupe :': 'Class / group:',
    'Rôle principal :': 'Main role:',
    'Rôles autorisés :': 'Authorized roles:',
    'Actions disponibles': 'Available actions',
    'Modifier mon mot de passe': 'Change my password',
    'Réinitialiser le mot de passe': 'Reset password',
    'Filtre période': 'Period filter',
    'Du': 'From',
    'Au': 'To',
    'Synthèse sur la période': 'Period summary',
    'Emprunts': 'Loans',
    'Inventaires utilisateur': 'User inventories',
    'Sorties validées comme magasinier': 'Checkouts validated as storekeeper',
    'Retours validés comme magasinier': 'Returns validated as storekeeper',
    'Interventions': 'Service reports',
    'Réparations': 'Repairs',
    'Actions réalisées en tant qu’utilisateur': 'Actions performed as user',
    'Actions réalisées en tant que magasinier': 'Actions performed as storekeeper',

    'Créer un bon d’intervention': 'Create a service report',
    'Enregistrer le bon d’intervention': 'Save service report',
    'Renseigner le bon de réparation': 'Complete repair report',
    'Enregistrer le bon de réparation': 'Save repair report',
    'Interventions récentes': 'Recent service reports',
    'Derniers bons de réparation': 'Latest repair reports',
    'Date': 'Date',
    'Résultat': 'Result',
    'Commentaire': 'Comment',
    'Constat :': 'Finding:',
    'Action :': 'Action:',
    'Pièces :': 'Parts:',
    'État final': 'Final condition',

    'Sauvegardes et restauration': 'Backups and restore',
    'Créer une sauvegarde manuelle': 'Create manual backup',
    'Restauration': 'Restore',
    'Archives disponibles': 'Available archives',
    'Télécharger': 'Download',
    'Restaurer': 'Restore',
    'Supprimer': 'Delete',
    'Aucune sauvegarde disponible.': 'No backup available.',

    'Droits ponctuels de modification matériel': 'Temporary equipment editing rights',
    'Autorisations existantes': 'Existing authorizations',
    'Période': 'Period',
    'Droits': 'Rights',
    'Prof': 'Teacher',
    'Aucune autorisation.': 'No authorization.',

    'Matériel sorti': 'Checked-out equipment',
    'Actualisation données : 5 s': 'Data refresh: 5 s',
    'Retard': 'Overdue',
    'Aucun matériel sorti.': 'No equipment checked out.',

    'Évaluation des compétences': 'Skills assessment',
    'Module expérimental : ToolMag observe les actions, propose des compétences et laisse la validation finale au professeur.': 'Experimental module: ToolMag observes actions, suggests skills and leaves final validation to the teacher.',
    'Filtres': 'Filters',
    'Exporter les évaluations Excel': 'Export assessments to Excel',
    'Séances pédagogiques': 'Teaching sessions',
    'Propositions automatiques': 'Automatic suggestions',

    'Bon état': 'Good condition',
    'Usure normale': 'Normal wear',
    'À surveiller': 'To be monitored',
    'Abîmé': 'Damaged',
    'Dangereux': 'Unsafe',
    'Absent': 'Missing',
    'Disponible': 'Available',
    'Sorti': 'Checked out',
    'En maintenance': 'Under maintenance',
    'Incomplet': 'Incomplete',
    'Hors service': 'Out of service',
    'Perdu': 'Lost',
    'Utilisateur': 'User',
    'Magasinier': 'Storekeeper',
    'Responsable': 'Supervisor',
    'Administrateur': 'Administrator'
  };

  function translateExact(text){
    const trimmed = text.replace(/\s+/g,' ').trim();
    return dict[trimmed] || null;
  }
  function walk(node){
    if (!node || ['SCRIPT','STYLE','TEXTAREA','INPUT'].includes(node.nodeName)) return;
    if (node.nodeType === Node.TEXT_NODE){
      const original = node.nodeValue;
      const translated = translateExact(original);
      if (translated){
        const leading = original.match(/^\s*/)[0];
        const trailing = original.match(/\s*$/)[0];
        node.nodeValue = leading + translated + trailing;
      }
      return;
    }
    node.childNodes.forEach(walk);
  }
  function translateInputs(){
    document.querySelectorAll('input[type="submit"], input[type="button"], button').forEach(el=>{
      const value = el.tagName === 'INPUT' ? el.value : el.textContent;
      const translated = translateExact(value);
      if (translated){
        if (el.tagName === 'INPUT') el.value = translated;
        else el.textContent = translated;
      }
    });
    document.querySelectorAll('input[placeholder], textarea[placeholder]').forEach(el=>{
      const translated = translateExact(el.getAttribute('placeholder'));
      if (translated) el.setAttribute('placeholder', translated);
    });
    document.querySelectorAll('option').forEach(el=>{
      const translated = translateExact(el.textContent);
      if (translated) el.textContent = translated;
    });
  }
  document.addEventListener('DOMContentLoaded', function(){
    walk(document.body);
    translateInputs();
    document.documentElement.lang = 'en';
  });
})();
