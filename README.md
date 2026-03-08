# InnerShift

InnerShift est un PoC local de clarification strategique personnelle. L'application transforme une parole libre en transcription, synthese structuree, indicateurs heuristiques, profil evolutif et rapport PDF premium.

## Fonctionnalites

- enregistrement micro directement depuis l'interface Streamlit
- import audio `.wav`, `.mp3`, `.m4a`
- transcription locale via `faster-whisper`
- analyse heuristique FR/EN basee sur des regles explicites
- historique des sessions et profil utilisateur consolide
- generation automatique d'un rapport PDF multi-pages
- onboarding guide en 4 couches (safety, intention, orientation, mini-module)

## Stack

- Python 3.11 ou 3.12 recommande
- Streamlit
- faster-whisper
- scikit-learn
- matplotlib
- ReportLab
- stockage local en JSON

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Notes :

- `Python 3.11` ou `3.12` est recommande pour une installation plus fluide des dependances audio et Whisper.
- `ffmpeg` est recommande et doit etre accessible dans le `PATH` pour normaliser les fichiers audio et supporter plus facilement les formats compreses.
- Au premier lancement de la transcription, `faster-whisper` telecharge le modele Whisper configure (`base` par defaut).

## Lancement

```bash
streamlit run app.py
```

Puis ouvrir l'URL indiquee par Streamlit dans le navigateur.

## Structure du projet

```text
.
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── data/
│   ├── audio/
│   ├── transcripts/
│   ├── reports/
│   ├── profiles/
│   ├── sessions/
│   └── onboarding/
├── assets/
│   ├── logo/
│   ├── styles/
│   └── templates/
└── modules/
    ├── audio_processing.py
    ├── transcription.py
    ├── text_cleaning.py
    ├── nlp_analysis.py
    ├── profile_manager.py
    ├── report_generator.py
    ├── storage.py
    ├── visualizations.py
    ├── session_manager.py
    └── utils.py
```

## Parcours du PoC

1. Creer une session et passer l'onboarding court (safety, intention, orientation, module guide).
2. Enregistrer sa voix ou importer un fichier audio pour la reflection libre.
3. Lancer la transcription Whisper, puis corriger legerement si besoin.
4. Generer l'analyse heuristique enrichie par le contexte onboarding.
5. Produire puis telecharger un rapport PDF premium avec plan 24h/7j/30j.

## Limites connues

- Le PoC est mono-utilisateur (`default_user`).
- Les scores et signaux sont heuristiques : ils servent a ouvrir des pistes de lecture, pas a produire un diagnostic.
- La qualite de transcription depend fortement de l'audio, du bruit ambiant et de la langue detectee.
- Sans `ffmpeg`, l'import reste possible mais certains formats et certaines metadonnees audio seront moins bien pris en charge.

## Evolutions envisageables

- ajouter une couche LLM de synthese ou de reformulation
- passer d'un stockage JSON a SQLite
- introduire plusieurs profils utilisateurs locaux
- enrichir le pipeline NLP avec embeddings, diarisation ou lexiques sectoriels
- ajouter des comparaisons de sessions, marqueurs temporels et routines de suivi

## Verifications rapides

Une fois les dependances installees :

```bash
python -m compileall .
streamlit run app.py
```
