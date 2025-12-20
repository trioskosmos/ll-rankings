#!/bin/bash

BASE_URL="http://localhost:8000/api/v1/submit"

echo "🧪 Testing Submission Endpoint"
echo "================================\n"

# Helper function
test_submission() {
  local name=$1
  local username=$2
  local franchise=$3
  local subgroup=$4
  local ranking=$5
  
  echo "📝 Test: $name"
  echo "Username: $username"
  
  response=$(curl -s -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"username\": \"$username\",
      \"franchise\": \"$franchise\",
      \"subgroup_name\": \"$subgroup\",
      \"ranking_list\": \"$ranking\"
    }")
  
  status=$(echo "$response" | jq -r '.status // .detail // "ERROR"')
  echo "Result: $status\n"
  
  echo "$response" | jq . 2>/dev/null || echo "$response"
  echo "\n---\n"
}

# Test 1: Valid submission
test_submission "Valid Submission" "alice" "liella" "All Songs" \
  "1. Starlight Prologue - Liella!\n2. Aspire - Liella!\n3. Dazzling Game - Liella!\n4. 真っ赤。 - Liella!\n5. 始まりは君の空 - Liella!"

# Test 2: Invalid franchise
test_submission "Invalid Franchise" "bob" "invalid" "All Songs" \
  "1. Starlight Prologue - Liella!"

# Test 3: Song not found
test_submission "Song Not Found" "charlie" "liella" "All Songs" \
  "1. Fake Song - Artist\n2. Another Fake - Artist\n3. Third Fake - Artist"

# Test 4: Conflicted submission (missing artist info)
test_submission "Invalid Format" "diana" "liella" "All Songs" \
  "1. Starlight Prologue\n2. Aspire\n3. Dazzling Game"

# Test 5: Ties
test_submission "With Ties" "eve" "liella" "All Songs" \
  "1. Starlight Prologue - Liella!\n1. Aspire - Liella!\n3. Dazzling Game - Liella!"

# Test 6: Empty username
test_submission "Empty Username" "" "liella" "All Songs" \
  "1. Starlight Prologue - Liella!"

echo "✅ Test suite complete! Check the database to verify submissions were saved."
