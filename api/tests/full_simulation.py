import httpx
import random
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
FRANCHISE = "liella"
SUBGROUP = "All Songs"

def get_real_songs():
    """Fetch the actual songs from the API to ensure 100% matching."""
    print("📡 Fetching master song list from API...")
    resp = httpx.get(f"{BASE_URL}/health/songs")
    return resp.json()["songs"]

def generate_ranking_text(songs, user_type="chaos"):
    """
    Generates a ranking string.
    Types: 
      - 'consensus': mostly alphabetical (simulating a common opinion)
      - 'chaos': completely random
      - 'starlight_stan': puts Starlight Prologue at #1 every time
    """
    local_songs = list(songs)
    
    if user_type == "chaos":
        random.shuffle(local_songs)
    elif user_type == "consensus":
        # Sort by name length + random jiggle to simulate 'patterned' taste
        local_songs.sort(key=lambda s: len(s['name']) + random.uniform(0, 5))
    elif user_type == "starlight_stan":
        # Find Starlight Prologue and move it to top
        starlight = next((s for s in local_songs if "Starlight Prologue" in s['name']), None)
        random.shuffle(local_songs)
        if starlight:
            local_songs.remove(starlight)
            local_songs.insert(0, starlight)

    lines = []
    for idx, song in enumerate(local_songs, start=1):
        # Construct the strict format: "1. Song Name - Artist Info"
        # We use a dummy artist since the matcher only cares about the song name part
        lines.append(f"{idx}. {song['name']} - Liella!")
    
    return "\n".join(lines)

def run_simulation(count=30):
    all_songs = get_real_songs()
    if not all_songs:
        print("❌ No songs found. Seed the database first!")
        return

    print(f"🚀 Starting simulation for {count} users...")
    
    with httpx.Client(timeout=30.0) as client:
        for i in range(count):
            # Assign user archetypes
            if i < 10: arche = "consensus"
            elif i < 20: arche = "chaos"
            else: arche = "starlight_stan"
            
            username = f"Fan_{arche}_{i+1}"
            
            payload = {
                "username": username,
                "franchise": FRANCHISE,
                "subgroup_name": SUBGROUP,
                "ranking_list": generate_ranking_text(all_songs, arche)
            }
            
            print(f"   [{i+1}/{count}] Submitting as {username} ({arche})...", end="\r")
            
            try:
                resp = client.post(f"{BASE_URL}/submit", json=payload)
                if resp.status_code != 200:
                    print(f"\n❌ Failed at {username}: {resp.text}")
            except Exception as e:
                print(f"\n❌ Error connecting: {e}")
                break

    print(f"\n✨ Simulation Complete. 30 submissions added to '{SUBGROUP}'.")
    print("👉 Next step: Wait for the scheduler OR manually trigger analysis.")

if __name__ == "__main__":
    run_simulation(30)