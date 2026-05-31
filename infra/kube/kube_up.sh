#!/bin/bash
#
# kube_up.sh — неблокирующий запуск всего стенда NBank в minikube.
#
# В отличие от restart_kube.sh (это runbook со списком команд для ручного
# копирования), этот скрипт можно запустить целиком:
#
#   bash kube_up.sh            # поднять всё (идемпотентно, можно запускать повторно)
#   bash kube_up.sh --clean    # пересоздать кластер с нуля (minikube delete) и поднять всё
#
# port-forward'ы запускаются в фоне (не блокируют консоль), их PID'ы пишутся
# в .pf-pids, логи — в .pf-logs/. Остановить всё: bash kube_down.sh
set -euo pipefail

# Работаем из каталога скрипта (infra/kube), откуда бы его ни запустили —
# чтобы относительные пути (./nbank-chart, *-values.yaml) всегда резолвились.
cd "$(dirname "$0")"

CLEAN=false
if [[ "${1:-}" == "--clean" ]]; then
  CLEAN=true
fi

PF_PIDS_FILE=".pf-pids"
PF_LOG_DIR=".pf-logs"

# --- helper: запустить port-forward в фоне и запомнить PID -------------------
start_pf() {
  # $1 — человекочитаемое имя (для имени лог-файла), далее — аргументы kubectl
  local name="$1"; shift
  mkdir -p "$PF_LOG_DIR"
  nohup kubectl port-forward "$@" > "$PF_LOG_DIR/$name.log" 2>&1 &
  echo "$!" >> "$PF_PIDS_FILE"
  echo "    port-forward [$name] pid=$! -> $PF_LOG_DIR/$name.log"
}

# --- helper: повтор команды при флаки-сети ----------------------------------
# helm.elastic.co и github.io иногда отдают 403 / context deadline exceeded.
# Повторяем команду до 5 раз с паузой, прежде чем считать её упавшей.
retry() {
  local n=1 max=5 delay=8
  until "$@"; do
    if [[ $n -ge $max ]]; then
      echo "    команда не удалась после $max попыток: $*" >&2
      return 1
    fi
    echo "    попытка $n/$max не удалась, повтор через ${delay}s..."
    sleep "$delay"
    n=$((n + 1))
  done
}

# ============================================================================
# ШАГ 0: (опционально) полный сброс кластера
# ============================================================================
if $CLEAN; then
  echo "==> [--clean] Полный сброс: minikube delete"
  minikube delete || true
  rm -f "$PF_PIDS_FILE"
fi

# Свежий файл PID'ов на каждый запуск (старые форварды снимет kube_down.sh)
: > "$PF_PIDS_FILE"

# ============================================================================
# ШАГ 1: кластер и сервисы приложения
# ============================================================================
echo "==> Запуск minikube (если уже запущен — no-op)"
minikube start --driver=docker

echo "==> ConfigMap selenoid-config (идемпотентно)"
kubectl create configmap selenoid-config \
  --from-file=browsers.json=./nbank-chart/files/browsers.json \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Helm релиз nbank"
helm upgrade --install nbank ./nbank-chart

echo "==> Ждём готовности сервисов приложения"
# Postgres должен подняться раньше backend: образ with_database падает на старте,
# если БД ещё недоступна (Flyway-миграции -> connection refused -> crashloop).
kubectl rollout status deployment/postgres     --timeout=300s
kubectl rollout status deployment/backend     --timeout=300s
kubectl rollout status deployment/frontend     --timeout=300s || true
kubectl rollout status deployment/selenoid     --timeout=300s || true
kubectl rollout status deployment/selenoid-ui --timeout=300s || true

# ============================================================================
# ШАГ 2: мониторинг (Prometheus + Grafana)
# ============================================================================
echo "==> Helm репозитории"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
helm repo add elastic https://helm.elastic.co || true
# helm repo update иногда таймаутит на github.io (context deadline exceeded).
# Это не критично: репозитории уже добавлены, версии чартов запиннены, индекс берётся из кэша.
# Пробуем обновить (с одним повтором), но при неудаче продолжаем с кэшированным индексом.
helm repo update || { echo "    WARN: индекс не обновился, повтор..."; sleep 5; helm repo update; } \
  || echo "    WARN: не удалось обновить индекс репозиториев — продолжаем с кэшем"

echo "==> Helm релиз monitoring (kube-prometheus-stack)"
# Известная гонка этого чарта: на свежем кластере Helm ставит CRD (ServiceMonitor и пр.),
# но в рамках того же вызова не успевает их "увидеть" -> "no matches for kind ServiceMonitor".
# Первый запуск регистрирует CRD, повторный — успешно создаёт ресурсы. Поэтому retry.
install_monitoring() {
  helm upgrade --install monitoring prometheus-community/kube-prometheus-stack --version 86.1.0 \
    -n monitoring --create-namespace -f monitoring-values.yaml
}
if ! install_monitoring; then
  echo "    CRD ещё не зарегистрированы — ждём и повторяем установку monitoring"
  kubectl wait --for=condition=Established --timeout=120s \
    crd/servicemonitors.monitoring.coreos.com crd/prometheuses.monitoring.coreos.com || true
  install_monitoring
fi

echo "==> Секрет backend-basic-auth (идемпотентно)"
kubectl create secret generic backend-basic-auth \
  --from-literal=username=admin --from-literal=password=admin \
  -n monitoring --dry-run=client -o yaml | kubectl apply -f -

echo "==> ServiceMonitor для backend"
kubectl apply -f spring-monitoring.yaml

# ============================================================================
# ШАГ 3: логирование (Elasticsearch + Kibana + Filebeat)
# ============================================================================
echo "==> Helm релиз elasticsearch"
retry helm upgrade --install elasticsearch elastic/elasticsearch --version 7.17.3 \
  -n logging --create-namespace -f elasticsearch-values.yaml

echo "==> Ждём готовности Elasticsearch (первый запуск тянет ~600MB образ — это долго)"
kubectl rollout status statefulset/elasticsearch-master -n logging --timeout=900s

echo "==> Helm релиз kibana"
retry helm upgrade --install kibana elastic/kibana --version 7.17.3 \
  -n logging -f kibana-values.yaml

echo "==> Helm релиз filebeat"
retry helm upgrade --install filebeat elastic/filebeat --version 7.17.3 \
  -n logging -f filebeat-values.yaml

echo "==> Ждём готовности Kibana (тоже тянет образ при первом запуске)"
kubectl rollout status deployment/kibana-kibana -n logging --timeout=600s || true

# ============================================================================
# ШАГ 4: проброс портов в фоне (консоль не блокируется)
# ============================================================================
echo "==> Запускаем port-forward'ы в фоне"
start_pf frontend    svc/frontend 3000:80
start_pf backend     svc/backend  4111:4111
# Postgres -> localhost:5433 для тестов с api_version=with_database
# (resources/config.properties: DB_HOST=localhost DB_PORT=5433).
start_pf postgres    svc/postgres 5433:5432
start_pf selenoid    svc/selenoid 4444:4444
start_pf selenoid-ui svc/selenoid-ui 8080:8080
start_pf prometheus  svc/monitoring-kube-prometheus-prometheus -n monitoring 3001:9090
start_pf grafana     svc/monitoring-grafana -n monitoring 3002:80
start_pf kibana      svc/kibana-kibana -n logging 5601:5601

echo
echo "============================================================"
echo " Готово. Сервисы доступны на:"
echo "   Frontend     http://localhost:3000"
echo "   Backend      http://localhost:4111"
echo "   Postgres     localhost:5433   (для тестов with_database)"
echo "   Selenoid UI  http://localhost:8080"
echo "   Prometheus   http://localhost:3001"
echo "   Grafana      http://localhost:3002   (admin/admin)"
echo "   Kibana       http://localhost:5601"
echo
echo " Остановить port-forward'ы и/или снести стенд: bash kube_down.sh"
echo "============================================================"
