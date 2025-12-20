# Love Live Songs Ranking system

A system for community song rankings and statistical analysis of the Love Live! discography. Converts raw user ranking lists into community consensus data.

## Core Metrics

The system calculates several metrics to understand community behavior:
*   **Consensus Leaderboard**: Calculated using the average of relativized ranks across all valid submissions.
*   **Spice Index**: A weighted Root Mean Square (RMS) distance measuring how unique a user's taste is compared to the group average.
*   **Controversy Index**: Combines Coefficient of Variation with a Bimodality Indicator to find songs that split the room.
*   **Divergence Matrix**: Pairwise taste distance between every community member.
*   **Hot Takes**: Identifies individual songs where a user deviates significantly from the mean.

## Setup

1.  **Start the services**:
    ```bash
    cd api
    docker-compose up -d
    ```

2.  **Seed the database**:
    The system automatically seeds songs and subgroups from `liella_songs.json` and `subgroups.toml` on first boot

3.  **Populate the database with rankings**:
    Use https://hamproductions.github.io/the-sorter/songs/ to generate rankings and then copy results to txt. Submission of these results will be done in frontend once thats implemented lol

5.  **Access the Frontend**:
    Open `test.html` in your browser to view the leaderboard and analysis suite
