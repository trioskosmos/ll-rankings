# Oshi Detector Technical Logic

This document outlines the logic and methods used to implement the **Solo-Only Oshi Detector**, ensuring member bias is calculated accurately using only individual song rankings.

## 1. Solo vs. Subunit Distinction
The system distinguishes "Solo" artists from "Subunits" or "Groups" by cross-referencing `Subgroups` in the database with `artists-info.json`.

- **Data Source**: `data/artists-info.json`
- **Logic**: An artist is considered a "Solo" if the `characters` list in their JSON definition has a length of exactly **1**.
- **Filter**: `if len(characters) == 1: # This is a Solo Artist`

## 2. Fuzzy Matching Algorithm
Subgroups in the database (often seeded from `subgroups_new.toml`) may use different naming conventions than the canonical artist names in `artists-info.json`.

### Matching Priority:
1.  **Exact Match**: Check if `subgroup.name` exactly matches either `name` (Japanese) or `englishName` in `artists-info.json`.
2.  **"Solos" Suffix Pattern**: If the subgroup name ends with `" Solos"` (e.g., `"Kanon Solos"`):
    -   Strip the suffix to get the `base_name` (e.g., `"Kanon"`).
    -   Iterate through all solo artists in `artists-info.json`.
    -   Check if the `base_name` is contained within the `englishName` (e.g., `"Kanon"` is in `"Kanon Shibuya"`).
    -   If a match is found, associate the subgroup's songs with that character ID.

## 3. Minimum Song Thresholds
To ensure that all relevant members appear in the results, especially newer members with limited discographies:

- **Config**: `len(cranks) < 1` (minimum 1 ranked song required).
- **Reasoning**: Previous logic required 3 songs, which excluded Gen 3 members or rivals like **Tomari Onitsuka** (1 solo), **Shiki Wakana** (2 solos), and **Natsumi Onitsuka** (2 solos). Lowering the threshold to 1 ensures 11/11 Liella members are detectable.

## 4. Frontend Integration
The Oshi Detector UI was streamlined to eliminate redundant actions:

- **Auto-Detection**: The `Detect Bias` button was removed.
- **Trigger**: An `onchange="analyzeBias()"` event was added to the user selection dropdown.
- **UX**: Selecting a user immediately refreshes the bias cards for all members.

## 5. Summary of Data Flow
1.  **Selection**: User selects a username from the dropdown.
2.  **Lookup**: Backend fetches the user's latest ranking submission.
3.  **Mapping**: All subgroups are scanned; "Solo" subgroups are identified via fuzzy matching to `artists-info.json`.
4.  **Math**: Average rank per character is calculated; Bias is calculated as `Global_Average - Character_Average`.
5.  **Render**: Resulting biases are displayed as member cards.
