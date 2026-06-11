#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://localhost:9000}"
echo "Test routage PFMP : $BASE/pfmp/"
curl -sI "$BASE/pfmp/" | tr -d '\r' | grep -Ei '^(HTTP/|X-LP-Gateway-Module:|Set-Cookie:|Location:)' || true
echo
echo "Test login PFMP : $BASE/pfmp/login/"
curl -sI "$BASE/pfmp/login/" | tr -d '\r' | grep -Ei '^(HTTP/|X-LP-Gateway-Module:|Set-Cookie:|Location:)' || true
echo
echo "Attendus : X-LP-Gateway-Module: pfmp ; cookie pfmp_csrftoken ou pfmp_sessionid ; aucune redirection vers un autre module."
