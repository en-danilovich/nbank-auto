#!/usr/bin/env bash
set -uo pipefail

# Runs API tests against a Docker Compose test environment.
#
# Flow:
#   1) Start the test environment (postgres + backend + frontend) via docker compose,
#      pointing the backend at a fraud-mock host that the tests container will expose.
#   2) Run the tests container with --rm, attached to the compose network and aliased
#      as "fraud-mock" so backend's fraud-detection calls land on it.
#   3) Tear the environment down — even if tests fail.
#
# Configurable via environment variables:
#   COMPOSE_FILE     - path to compose file (default: infra/docker-compose/docker-compose.yaml)
#   COMPOSE_PROJECT  - compose project name (default: docker-compose)
#   TESTS_IMAGE      - tests image to run (default: edanilovich/nbank-tests:latest)
#   APIBASEURL       - API URL passed to the tests container (default: http://backend:4111)
#   UIBASEURL        - UI URL passed to the tests container  (default: http://frontend)
#   FRAUD_ALIAS      - network alias for tests container, used by backend (default: fraud-mock)

COMPOSE_FILE="${COMPOSE_FILE:-infra/docker-compose/docker-compose.yaml}"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-docker-compose}"
TESTS_IMAGE="${TESTS_IMAGE:-edanilovich/nbank-tests:latest}"
APIBASEURL="${APIBASEURL:-http://backend:4111}"
UIBASEURL="${UIBASEURL:-http://frontend}"
FRAUD_ALIAS="${FRAUD_ALIAS:-fraud-mock}"
NETWORK_NAME="${COMPOSE_PROJECT}_nbank-network"

# Tell the backend where to find the fraud service. The tests container joins the
# same compose network with this alias, so this hostname resolves to the tests.
export FRAUD_DETECTION_SERVICE_URL="http://${FRAUD_ALIAS}:8080"

log() {
  echo ""
  echo "==> $*"
}

cleanup() {
  local exit_code=$?
  log "Stopping test environment"
  docker compose -p "${COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" down --remove-orphans || true
  if [[ ${exit_code} -eq 0 ]]; then
    log "Done. All tests passed."
  else
    log "Done. Tests finished with exit code ${exit_code}."
  fi
  exit "${exit_code}"
}

trap cleanup EXIT INT TERM

log "Starting test environment from ${COMPOSE_FILE}"
log "  FRAUD_DETECTION_SERVICE_URL=${FRAUD_DETECTION_SERVICE_URL}"
docker compose -p "${COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" up -d --force-recreate --wait

log "Running tests in container ${TESTS_IMAGE}"
log "  network=${NETWORK_NAME} alias=${FRAUD_ALIAS}"
log "  APIBASEURL=${APIBASEURL}"
log "  UIBASEURL=${UIBASEURL}"

docker run --rm \
  --network "${NETWORK_NAME}" \
  --network-alias "${FRAUD_ALIAS}" \
  -e APIBASEURL="${APIBASEURL}" \
  -e UIBASEURL="${UIBASEURL}" \
  "${TESTS_IMAGE}" \
  pytest -m api --api-version with_fraud_check
