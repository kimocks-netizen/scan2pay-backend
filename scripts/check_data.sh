#!/bin/bash
API="https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod"

VENDOR_TOKEN=$(curl -s -X POST "${API}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"identifier":"0821000001","password":"Vendor1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

TIP_TOKEN=$(curl -s -X POST "${API}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"identifier":"0660404333","password":"123456"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

ADMIN_TOKEN=$(curl -s -X POST "${API}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"identifier":"0616583827","password":"Admin1234"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "=== VENDOR transactions (first 2) ==="
curl -s "${API}/transactions?limit=2" -H "Authorization: Bearer ${VENDOR_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "=== TIP transactions (first 2) ==="
curl -s "${API}/transactions?limit=2" -H "Authorization: Bearer ${TIP_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "=== ADMIN transactions (first 2) ==="
curl -s "${API}/admin/transactions?limit=2" -H "Authorization: Bearer ${ADMIN_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "=== ADMIN merchants ==="
curl -s "${API}/admin/merchants?limit=10" -H "Authorization: Bearer ${ADMIN_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "=== ADMIN balance ==="
curl -s "${API}/admin/balance" -H "Authorization: Bearer ${ADMIN_TOKEN}" | python3 -m json.tool 2>/dev/null
