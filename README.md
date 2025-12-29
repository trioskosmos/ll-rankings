# Love Live Songs Ranking System

A comprehensive system for community song rankings and statistical analysis of the Love Live! discography. Converts raw user ranking lists into community consensus data with advanced social analytics.

## Features

### Core Analysis
*   **Consensus Leaderboard**: Community-aggregated rankings using average relativized ranks
*   **Spice Index**: Measures how unique each user's taste is compared to the group
*   **Controversy Index**: Identifies songs that split the community (high variance)
*   **Divergence Matrix**: Pairwise taste distance between all users
*   **Hot Takes/Sleepers**: Individual songs where users deviate significantly from consensus

### Advanced Social Features (New!)
*   **Head-to-Head Duel**: Direct comparison between any two users with compatibility score
*   **Soulmate/Nemesis Finder**: Automatically find users with most similar or opposite taste
*   **Oshi Bias Detector**: Analyzes which group members you subconsciously favor
*   **Taste Constellation**: Real-time force-directed graph showing community clusters
*   **Conformity Index**: Backend analysis for Normie/Hipster classification

## Setup

### Quick Start (Local Development)

1.  **Start the API server**:
    ```bash
    cd api
    pip install -r requirements.txt
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

2.  **Database**:
    The system uses SQLite by default and automatically seeds from:
    - `data/song-info.json` - Song catalog
    - `data/artists-info.json` - Artist/member mappings
    - `api/app/seeds/user_rankings.csv` - Sample user rankings

3.  **Access the Frontend**:
    Open `index.html` in your browser (or serve via any static file server)

### Docker Setup

```bash
cd api
docker-compose up -d
```

## Tech Stack

- **Backend**: Python/FastAPI with SQLAlchemy ORM
- **Frontend**: Vanilla HTML/CSS/JS (no build step required)
- **Database**: SQLite (default) or PostgreSQL
- **Visualization**: HTML5 Canvas for force-directed graphs

---

## Changelog

### v0.2.0 - Advanced Analytics Update (2025-12-30)

#### 🚀 New Features

**Backend (`api/app/services/analysis.py`)**
- Added `compute_head_to_head()` - Direct user comparison with compatibility scoring
- Added `compute_user_match()` - Soulmate/Nemesis detection using divergence matrix
- Added `compute_oshi_bias()` - Member favoritism analysis using artist metadata
- Added `compute_conformity()` - Normie/Hipster index based on consensus deviation

**New API Endpoints (`api/app/api/v1/analysis.py`)**
- `GET /analysis/head-to-head` - Compare two users directly
- `GET /analysis/user-match` - Find soulmates and nemeses for a user
- `GET /analysis/oshi-bias` - Get member bias analysis for a user
- `GET /analysis/conformity` - Get conformity rankings for all users

**Frontend (`index.html`)**
- **Rivals Tab**: New dedicated tab for social comparison features
  - Head-to-Head Duel widget with compatibility score and dispute list
  - Match Finder to discover soulmates and nemeses
  - Oshi Detector to reveal member bias with visual cards
  - Taste Constellation - Animated force-directed graph showing user clusters

#### ⚡ Performance Improvements
- **Data Caching**: Added client-side cache to prevent redundant API requests
  - Tab switches now instant after initial load
  - Cache invalidated on franchise/subgroup change
- **Optimized API Calls**: Parallel fetching for initial data load

#### 🐛 Bug Fixes
- Fixed redundant API calls on every tab click
- Fixed subgroup change not refreshing data properly
- Removed orphaned try-catch blocks from JS
- Fixed user dropdown population in Rivals tab

#### 🔧 Technical Changes
- Added `json` and `os` imports to analysis service for metadata loading
- Integrated `artists-info.json` for member-to-song correlation
- Added `changeSubgroupView()` function for proper cache handling
- Updated `.gitignore` to exclude SQLite database files

#### 📝 Documentation
- Updated README with new features and setup instructions
- Added comprehensive changelog

---

### v0.1.0 - Initial Release

- Core ranking system with consensus calculation
- Spice Index and Controversy metrics
- Divergence Matrix visualization
- Hot Takes analysis
- Multi-franchise support (Liella, Aqours, μ's, Nijigasaki, Hasunosora)

## License

MIT
