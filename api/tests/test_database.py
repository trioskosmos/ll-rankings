import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

def verify_seeding():
    print("Starting Seeding Verification...\n")
    
    with httpx.Client() as client:
        # 1. Basic Health Check
        print("Checking API Connectivity...")
        try:
            health = client.get(f"{BASE_URL}/health")
            health.raise_for_status()
            print(f"API Status: {health.json()['status']}")
            print(f"DB Status:  {health.json()['database']}")
        except Exception as e:
            print(f"API unreachable: {e}")
            return

        # 2. Database Diagnostics
        print("\nFetching Database Diagnostics...")
        diag = client.get(f"{BASE_URL}/health/database")
        data = diag.json()
        
        verification = data.get("verification", {})
        liella = data.get("liella", {})
        
        print(f"   - Franchise 'liella' exists: {liella['franchise_exists']}")
        print(f"   - Songs found: {liella['songs']} / {verification['expected_songs']}")
        print(f"   - Subgroups found: {liella['subgroups']} / {verification['expected_subgroups']}")
        
        if verification.get("all_pass"):
            print("DATABASE VERIFICATION PASSED")
        else:
            print("DATABASE VERIFICATION INCOMPLETE")

        # 3. Subgroup Breakdown
        print("\nSubgroup Breakdown:")
        subgroups = data.get("subgroups_detail", [])
        for sg in subgroups:
            custom_label = "[Custom]" if sg["is_custom"] else "[Static]"
            print(f"   {custom_label:9} {sg['name']:25} ({sg['song_count']} songs)")

        # 4. Sample Song Check
        print("\nChecking Sample Songs...")
        songs_resp = client.get(f"{BASE_URL}/health/songs")
        songs_data = songs_resp.json()
        all_songs = songs_data.get("songs", [])
        
        if all_songs:
            print(f"   Total songs in list: {len(all_songs)}")
            print("   First 3 songs:")
            for s in all_songs[:3]:
                print(f"     - {s['name']}")
        else:
            print("   No songs returned.")

if __name__ == "__main__":
    verify_seeding()
