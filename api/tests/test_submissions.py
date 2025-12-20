import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

def run_test(name, payload):
    print(f"Testing: {name}")
    try:
        with httpx.Client() as client:
            resp = client.post(f"{BASE_URL}/submit", json=payload)
            print(f"   Status: {resp.status_code}")
            print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    print("-" * 40)

# 1. SUCCESS: Perfect format
valid_payload = {
    "username": "RenHazuki",
    "franchise": "liella",
    "subgroup_name": "All Songs",
    "ranking_list": (
        "1. Starlight Prologue - Liella!\n"
        "2. 始まりは君の空 - Liella!\n"
        "3. 未来は風のように - Liella!"
    )
}

# 2. CONFLICT: Song typo (Prolouge instead of Prologue)
typo_payload = {
    **valid_payload,
    "username": "Keke",
    "ranking_list": "1. Starlight Prolouge - Liella!\n2. 始まりは君の空 - Liella!\n3. 未来は風のように - Liella!"
}

# 3. CONFLICT: Formatting error (missing rank/hyphen)
format_payload = {
    **valid_payload,
    "username": "Kanon",
    "ranking_list": "Starlight Prologue - Liella!\n2. 始まりは君の空 - Liella!"
}

# 4. CONFLICT: Duplicate song
duplicate_payload = {
    **valid_payload,
    "username": "Natsumi",
    "ranking_list": (
        "1. Starlight Prologue - Liella!\n"
        "2. Starlight Prologue - Liella!\n"
        "3. 始まりは君の空 - Liella!"
    )
}

if __name__ == "__main__":
    run_test("Perfect Submission", valid_payload)
    run_test("Song Name Typo", typo_payload)
    run_test("Format Error", format_payload)
    run_test("Duplicate Song", duplicate_payload)