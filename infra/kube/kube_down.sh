#!/bin/bash
#
# kube_down.sh — остановка стенда NBank.
#
#   bash kube_down.sh          # снять фоновые port-forward'ы + удалить релизы и namespace'ы
#   bash kube_down.sh --all    # то же + полностью удалить кластер (minikube delete)
#
# Парный скрипт к kube_up.sh.
set -uo pipefail

cd "$(dirname "$0")"

PF_PIDS_FILE=".pf-pids"
PF_LOG_DIR=".pf-logs"

# --- 1. Снимаем фоновые port-forward'ы --------------------------------------
# Сначала аккуратно гасим PID'ы, записанные kube_up.sh (frontend, backend,
# postgres, selenoid, мониторинг, kibana — все start_pf пишут сюда).
if [[ -f "$PF_PIDS_FILE" ]]; then
  echo "==> Останавливаем port-forward'ы из $PF_PIDS_FILE"
  while read -r pid; do
    [[ -n "$pid" ]] || continue
    if kill "$pid" 2>/dev/null; then
      echo "    killed pid=$pid"
    fi
  done < "$PF_PIDS_FILE"
  rm -f "$PF_PIDS_FILE"
fi

# Подстраховка: гасим любые оставшиеся kubectl port-forward — например, форварды,
# запущенные руками вне kube_up.sh (их нет в $PF_PIDS_FILE), или хвосты с прошлых
# запусков. Выполняется всегда, не только когда файла PID'ов нет.
echo "==> Подчищаем оставшиеся kubectl port-forward (если есть)"
pkill -f "kubectl port-forward" 2>/dev/null || true

rm -rf "$PF_LOG_DIR"

# --- 2. Полный снос кластера? -----------------------------------------------
if [[ "${1:-}" == "--all" ]]; then
  echo "==> [--all] minikube delete (удаляем весь кластер)"
  minikube delete || true
  echo "==> Готово: кластер удалён."
  exit 0
fi

# --- 3. Точечный снос: удаляем релизы и namespace'ы -------------------------
echo "==> Удаляем Helm релизы"
helm uninstall filebeat       -n logging    2>/dev/null || true
helm uninstall kibana         -n logging    2>/dev/null || true
helm uninstall elasticsearch -n logging    2>/dev/null || true
helm uninstall monitoring     -n monitoring 2>/dev/null || true
helm uninstall nbank                         2>/dev/null || true

echo "==> Удаляем namespace'ы logging и monitoring"
kubectl delete namespace logging    --ignore-not-found
kubectl delete namespace monitoring --ignore-not-found

echo "==> Удаляем ресурсы приложения в default"
kubectl delete configmap selenoid-config --ignore-not-found

echo "==> Готово. Кластер minikube оставлен запущенным (полный снос: bash kube_down.sh --all)."
