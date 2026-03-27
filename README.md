# OmniStream 🎵

**Agrégation unifiée d'historique d'écoute musicale multi-plateforme avec dashboard interactif.**

Collectez vos données musicales depuis **5 plateformes** (Spotify, Deezer, Amazon Music, YouTube Music, SoundCloud) avec support **multi-comptes**, centralisez-les dans une base SQLite, et explorez-les via un dashboard moderne et interactif.

## ✨ Caracteristiques

- 🎯 **Multi-plateforme** : Aggrege Spotify, Deezer, Amazon Music, YouTube Music, SoundCloud
- 👥 **Multi-comptes** : Support complet des multi-comptes par plateforme
- 🔄 **Idempotent** : Exécutez le pipeline plusieurs fois sans doublon
- 🧹 **Déduplication intelligente** : Fuzzy matching + ISRC + normalisation texte
- 📊 **Dashboard interactif** : Next.js + Tremor + Recharts
- 🔐 **RGPD-first** : Export légal de vos données personnelles
- 🏗️ **Schéma étoile** : Base SQLite optimisée pour les analyses
- ✅ **Entièrement testé** : 27 tests unitaires + intégration

## 🚀 Quick Start

### Prérequis

- Python 3.11+
- Node.js 18+ (pour le dashboard)
- Git

### Installation

```bash
# Cloner le repo
git clone https://github.com/<ton-username>/OmniStream.git
cd OmniStream

# Setup ETL Python
cd etl
pip install -e ".[dev]"
python -m pytest tests/ -v  # Vérifier que tout fonctionne

cd ..
```

### Utilisation - Pipeline ETL

1. **Lancer vos exports RGPD** :
   - Spotify : Paramètres > Confidentialité > "Demander mes données étendues" (15-30 jours)
   - Deezer : Paramètres > Mes données > Demander mes données
   - Amazon Music : Gérer votre contenu et vos appareils > Demande de données
   - YouTube Music : takeout.google.com > "YouTube et YouTube Music"
   - SoundCloud : Data & Privacy > Request your data

2. **Placer les exports dans** `data/exports/<plateforme>/`

3. **Exécuter le pipeline** :
   ```bash
   cd etl
   python -m src.pipeline config.json
   ```

4. **Vérifier les résultats** :
   ```sql
   sqlite3 ../data/omnistream.db "SELECT COUNT(*) FROM fact_streams;"
   ```

### Configuration

Créer `etl/config.json` (copier depuis `config.example.json`) :

```json
[
    {
        "platform": "spotify",
        "account_id": "spotify_perso",
        "export_dir": "../data/exports/spotify_perso"
    },
    {
        "platform": "deezer",
        "account_id": "deezer_perso",
        "export_dir": "../data/exports/deezer_perso"
    }
]
```

## 📋 Architecture

### Data Flow

```
Exports RGPD (JSON/CSV)
  ↓
Parsers (Spotify, Deezer, YouTube, Amazon, SoundCloud)
  ↓
Normalisation (accents, feat., remaster)
  ↓
Loader (idempotent + dédup)
  ↓
SQLite Star Schema
```

### Structure du Projet

```
OmniStream/
├── etl/                          # Pipeline Python
│   ├── src/
│   │   ├── parsers/              # Un parser par plateforme
│   │   ├── api/                  # Clients OAuth (futur)
│   │   ├── models.py             # Pydantic schemas
│   │   ├── normalize.py          # Normalisation texte
│   │   ├── load.py               # Loader SQLite
│   │   ├── db.py                 # Connexion DB
│   │   ├── pipeline.py           # Orchestrateur
│   │   └── schema.sql            # Star schema
│   ├── tests/                    # Tests unitaires + fixtures
│   ├── pyproject.toml            # Dépendances
│   └── config.example.json       # Config template
│
├── dashboard/                    # Frontend Next.js
│   ├── src/
│   │   ├── app/                  # App Router
│   │   ├── components/           # Composants React
│   │   └── lib/                  # Utilitaires (DB, etc)
│   └── (à initialiser)
│
├── data/
│   ├── exports/                  # Fichiers RGPD (gitignored)
│   └── omnistream.db             # SQLite (gitignored)
│
└── CLAUDE.md                     # Documentation pour Claude Code
```

### Base de Données (Star Schema)

**Dimensions :**
- `dim_artists` — Artistes uniques
- `dim_tracks` — Morceaux uniques
- `dim_genres` — Genres
- `dim_accounts` — Comptes multi-plateforme
- `dim_playlists` — Snapshots de playlists

**Faits :**
- `fact_streams` — Chaque ligne = 1 écoute (grain : `track_id`, `timestamp`, `account_id`)

**Support :**
- `track_genres` — Many-to-many tracks ↔ genres
- `playlist_tracks` — Many-to-many playlists ↔ tracks
- `track_features` — Audio features (valence, energy, etc.)
- `dedup_overrides` — Résolutions manuelles de fuzzy match

## 🧪 Tests

```bash
cd etl

# Tous les tests
python -m pytest tests/ -v

# Tests spécifiques
python -m pytest tests/test_parsers.py::TestSpotifyParser -v
python -m pytest tests/test_load.py::TestLoadStreams::test_idempotent_reinsert -v

# Avec coverage
python -m pytest tests/ --cov=src --cov-report=html
```

**27 tests passants :**
- ✅ Parsers (Spotify, YouTube)
- ✅ Normalisation texte (accents, feat., remaster)
- ✅ Loader + idempotence
- ✅ Déduplication artiste/track

## 📦 Stack Technique

### Backend ETL
- **Python 3.11+**
- **Polars** — Traitement de données haute-performance
- **RapidFuzz** — Fuzzy matching
- **Pydantic** — Validation de schémas
- **musicbrainzngs** — Enrichissement données
- **SQLite** — Base de données
- **pytest** — Tests

### Frontend Dashboard
- **Next.js 14+** — React + fullstack
- **Tailwind CSS** — Styling
- **Shadcn/ui** — Composants UI
- **Tremor** — Dashboard components
- **Recharts** — Graphiques
- **better-sqlite3** — Accès SQLite depuis Node.js

## 🗺️ Roadmap

### Phase 0 ✅ (Terminée)
- [x] Structure du projet
- [x] Schéma SQLite
- [x] Parsers RGPD (5 plateformes)
- [x] Normalisation + dédup
- [x] 27 tests passants

### Phase 1 (En cours)
- [ ] Clients API playlists (Spotify, Deezer, YouTube)
- [ ] Scaffold dashboard Next.js
- [ ] Page Overview (KPIs)
- [ ] ListenBrainz intégration (ingestion continue)

### Phase 2 (À venir)
- [ ] Enrichissement MusicBrainz/Last.fm
- [ ] Pages Top Charts + Heatmap
- [ ] Mood Timeline (évolution humeur)
- [ ] Artist Deep Dive (fidélité artiste)

### Phase 3 (À venir)
- [ ] Clustering K-Means
- [ ] Platform Comparison
- [ ] Cron pour ingestion continue

### Phase 4 (À venir)
- [ ] Docker Compose
- [ ] (Optionnel) Audio features (Essentia)
- [ ] (Optionnel) Export/partage

## ⚙️ Commandes Usuelles

```bash
# Tests ETL
cd etl && python -m pytest tests/ -v

# Lint
cd etl && ruff check src/ tests/

# Pipeline ETL
cd etl && python -m src.pipeline config.json

# Dashboard (après Node.js install)
cd dashboard && npm run dev
```

## 🤝 Contribuer

1. Fork le repo
2. Crée une branche (`git checkout -b feature/amazing-feature`)
3. Commit tes changements (`git commit -m 'Add amazing feature'`)
4. Push ta branche (`git push origin feature/amazing-feature`)
5. Ouvre une Pull Request

## 📝 Conventions

- **Code** : Anglais
- **Conversations** : Français
- **Stack Python** : Polars (pas Pandas), Pydantic, type hints obligatoires
- **Tests** : 1 fixture par plateforme, tests DB en `:memory:`
- **DB** : Star schema, idempotent loads, indices sur colonnes de jointure

## 🚨 Points Importants

### Challenges Connus

1. **Amazon Music** : Export très parcellaire (pas de `ms_played`)
2. **YouTube Music** : Pas de durée d'écoute dans l'export
3. **SoundCloud** : API fermée aux nouveaux devs (RGPD only)
4. **Spotify Audio Features** : Accès restreint pour nouvelles apps (fallback = MusicBrainz)

### Solutions Implémentées

- Normalisation texte robuste (accents, featured artists, remaster tags)
- Fuzzy matching + ISRC + MusicBrainz pour déduplication
- Parser flexible pour gérer variations de colonnes/dates
- Loader idempotent (re-run safe)

## 📊 Exemples de Requêtes SQL

```sql
-- Artiste le plus écouté
SELECT da.name, COUNT(*) as listen_count
FROM fact_streams fs
JOIN dim_tracks dt ON fs.track_id = dt.track_id
JOIN dim_artists da ON dt.artist_id = da.artist_id
GROUP BY da.artist_id
ORDER BY listen_count DESC;

-- Musique par jour de la semaine
SELECT strftime('%w', fs.timestamp) as dow, COUNT(*) as count
FROM fact_streams fs
WHERE fs.category = 'music'
GROUP BY dow;

-- Évolution temporelle par plateforme
SELECT DATE(fs.timestamp) as date, fs.platform, COUNT(*) as streams
FROM fact_streams fs
GROUP BY DATE(fs.timestamp), fs.platform
ORDER BY date;
```

## 📄 Licence

MIT License - See LICENSE file for details

## 📞 Support

Pour des questions ou issues :
- Ouvre une [GitHub Issue](https://github.com/<ton-username>/OmniStream/issues)
- Consulte le [CLAUDE.md](./CLAUDE.md) pour la documentation développeur

---

**Made with ❤️ by Lucas**

Retrouve-moi sur GitHub : [@LucasUsername](https://github.com/<ton-username>)
