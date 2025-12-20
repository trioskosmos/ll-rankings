import httpx
import random
import json

BASE_URL = "http://localhost:8000/api/v1"
FRANCHISE = "liella"
SUBGROUP = "All Songs"

def get_real_songs():
    print("📡 Synchronizing with API master list...")
    resp = httpx.get(f"{BASE_URL}/health/songs")
    return resp.json()["songs"]

def create_ranking_payload(sorted_songs, ties_frequency=0.0):
    """
    Constructs a ranking list string.
    ties_frequency: 0.0 to 1.0 probability of a song sharing a rank.
    """
    lines = []
    current_rank = 1
    for i, song in enumerate(sorted_songs):
        if i > 0 and random.random() < ties_frequency:
            # Create a tie by reusing the current_rank
            pass
        else:
            # Advance rank to the current index position
            current_rank = i + 1
            
        lines.append(f"{current_rank}. {song['name']} - Liella!")
    
    return "\n".join(lines)

def simulate_community(user_count=40):
    all_songs = get_real_songs()
    if not all_songs:
        print("❌ No songs found in database. Run seeds first.")
        return

    # Pick Battleground songs to test Bimodality/Controversy
    battleground_songs = random.sample(all_songs, 3)
    bg_names = [s['name'] for s in battleground_songs]
    print(f"🔥 Battleground songs for this run: {bg_names}")

    print(f"🚀 Injecting {user_count} complex archetypes into Liella rankings...")

    with httpx.Client(timeout=60.0) as client:
        for i in range(user_count):
            local_songs = list(all_songs)
            ties_freq = 0.0
            
            # --- ARCHETYPE LOGIC ---
            if i < 15:
                archetype = "Normie"
                local_songs.sort(key=lambda s: s['name'])
                for _ in range(10): # Minor jitter
                    idx = random.randint(0, len(local_songs)-2)
                    local_songs[idx], local_songs[idx+1] = local_songs[idx+1], local_songs[idx]

            elif i < 25:
                archetype = "Elitist"
                local_songs.sort(key=lambda s: s['name'], reverse=True)
                random.shuffle(local_songs[:20]) 

            elif i < 30:
                archetype = "Starlight_Coven"
                random.shuffle(local_songs)
                for s_name in bg_names:
                    s_obj = next(x for x in local_songs if x['name'] == s_name)
                    local_songs.remove(s_obj)
                    local_songs.insert(0, s_obj) 

            elif i < 35:
                archetype = "Anti_Starlight"
                random.shuffle(local_songs)
                for s_name in bg_names:
                    s_obj = next(x for x in local_songs if x['name'] == s_name)
                    local_songs.remove(s_obj)
                    local_songs.append(s_obj) 

            else:
                archetype = "Tie_Heavy"
                random.shuffle(local_songs)
                ties_freq = 0.4 

            username = f"{archetype}_{i+1}_{random.randint(100,999)}"
            # FIX: Only passing the required two arguments
            ranking_text = create_ranking_payload(local_songs, ties_freq)
            
            payload = {
                "username": username,
                "franchise": FRANCHISE,
                "subgroup_name": SUBGROUP,
                "ranking_list": ranking_text
            }

            print(f"   [{i+1}/{user_count}] Posting {username}...", end="\r")
            
            resp = client.post(f"{BASE_URL}/submit", json=payload)
            if resp.status_code != 200:
                print(f"\n❌ Error for {username}: {resp.text}")

    print(f"\n✨ Community simulation finished.")
    print("👉 Triggering weighted analytical recomputation...")
    
    # Use a separate context to ensure background task is triggered
    try:
        trigger = httpx.post(f"{BASE_URL}/analysis/trigger")
        if trigger.status_code == 200:
            print("✅ Background job started successfully. Check logs for progress.")
        else:
            print(f"⚠️  Trigger returned: {trigger.status_code} - {trigger.text}")
    except Exception as e:
        print(f"❌ Could not trigger recomputation: {e}")

if __name__ == "__main__":
    simulate_community(40)