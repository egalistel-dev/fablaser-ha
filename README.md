# FabLaser pour Home Assistant

Intégration [HACS](https://hacs.xyz) qui relie le logiciel de gravure **FabLaser** à Home Assistant.
FabLaser envoie son état à un webhook de Home Assistant : aucun port à ouvrir sur le PC de gravure, aucun jeton à stocker.

## Ce que tu obtiens

Un appareil **FabLaser** avec ces entités (elles gardent leur dernière valeur après un redémarrage de Home Assistant) :

| Entité | Contenu |
|---|---|
| État | Hors ligne, Connecté, Gravure en cours, En pause, Terminé, Erreur, Arrêté |
| Avancement | Pourcentage de la gravure en cours |
| Temps restant | En minutes |
| Durée de la dernière gravure | En minutes |
| Fichier | Nom du projet gravé |
| Dernière erreur | Texte de l'erreur de la dernière gravure interrompue |
| Gravure en cours | Allumé pendant une gravure ou une pause |
| Machine connectée | Allumé quand FabLaser est connecté à la machine |
| Plateau (caméra) | Dernière image de la caméra du plateau, si tu actives l'envoi dans FabLaser (voir plus bas) |

« Hors ligne » veut dire que FabLaser est fermé ou que la machine est déconnectée.

Deux événements sont aussi émis, utilisables dans les automatisations :

- `fablaser_job_started` au début d'une gravure ;
- `fablaser_job_finished` à la fin, avec `result` (`termine`, `erreur` ou `arret`), `file`, `duration_min` et `error`.

## Installation

1. HACS > Intégrations > menu ⋮ > Dépôts personnalisés : ajoute l'adresse `https://github.com/egalistel-dev/fablaser-ha`, catégorie *Intégration*, puis installe **FabLaser**.
2. Redémarre Home Assistant.
3. Paramètres > Appareils et services > Ajouter une intégration > **FabLaser**. Donne un nom à l'appareil.
4. L'assistant affiche l'adresse du webhook. Copie-la.
5. Dans FabLaser : Préférences > Home Assistant > coche « Activer la liaison », colle l'adresse dans **Adresse du webhook**, puis clique sur « Tester la liaison ».

L'état apparaît dès que tu connectes ta machine dans FabLaser.

## Caméra du plateau (facultatif)

FabLaser peut envoyer l'image de sa caméra USB, celle qui voit le plateau, à Home Assistant. Dans FabLaser : Préférences > Home Assistant, coche « Envoyer l'image de la caméra du plateau à Home Assistant ». Une image part toutes les 4 secondes, seulement quand la caméra est allumée dans FabLaser et que la machine est connectée. L'entité `camera.fablaser_plateau` garde la dernière image, et devient indisponible quand tu éteins la caméra ou fermes FabLaser. L'image n'est jamais enregistrée par l'intégration.

Pour l'afficher sur un tableau de bord : carte « Image » (`picture-entity`) avec l'entité `camera.fablaser_plateau`. Home Assistant rafraîchit une image fixe environ toutes les 10 secondes.

## Exemple d'automatisation

```yaml
automation:
  - alias: Gravure terminée
    trigger:
      - platform: event
        event_type: fablaser_job_finished
    action:
      - service: notify.mobile_app_mon_telephone
        data:
          title: FabLaser
          message: >
            {% if trigger.event.data.result == 'termine' %}
              Gravure terminée : {{ trigger.event.data.file }}
            {% else %}
              Gravure interrompue ({{ trigger.event.data.result }}) {{ trigger.event.data.error }}
            {% endif %}
```

## Format des messages

FabLaser envoie un `POST` JSON à `/api/webhook/<identifiant>` ; les champs absents ne changent pas :

```json
{"state": "gravure", "progress": 42, "remaining_min": 12, "duration_min": null,
 "file": "porte-cle", "error": "", "version": "0.42.0", "machine": "Falcon 2 Pro", "connected": true}
```

Un `POST` dont le `Content-Type` est `image/jpeg` envoie à la place une image brute (2 Mo au plus) pour l'entité caméra. `{"camera": false}` efface l'image.
