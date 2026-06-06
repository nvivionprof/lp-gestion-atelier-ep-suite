# Note sur le fichier docker-compose.yml

Le fichier `docker-compose.yml` définit l’architecture cible, mais il ne sera exécutable que lorsque chaque dossier `services/*` contiendra au minimum :

- un `Dockerfile` ;
- une application Django ou un service web ;
- les dépendances nécessaires ;
- une commande de lancement.

Tant que les applications réelles ne sont pas ajoutées, ce dépôt doit être considéré comme un squelette de projet.
