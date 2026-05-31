#!/bin/bash

# ШАГ 1: поднятие сервисов приложения

# Запустили локальный Kubernetes-кластер с помощью minikube, используя Docker как драйвер
# (кластер будет запущен внутри докер контейнера)
minikube start --driver=docker

# Создали ConfigMap с именем selenoid-config, файл будет доступен под ключом browsers.json
kubectl create configmap selenoid-config --from-file=browsers.json=./nbank-chart/files/browsers.json

# Устанавливаем Helm чарт с именем релиза nbank, беря шаблоны из ./nbank-chart
# Это создаст все ресурсы, описанные в шаблонах Helm (Deployment, Service)
helm install nbank ./nbank-chart

# Все сервисы в namespace=default
kubectl get svc

# Все поды в namespace=default
kubectl get pods

# Логи конкретного сервиса
kubectl logs deployment/backend

# Проброс портов на локальную машину
kubectl port-forward svc/frontend 3000:80 #  > /dev/null 2>&1 & (проброс порта в фоновом режиме)
kubectl port-forward svc/backend 4111:4111
kubectl port-forward svc/selenoid 4444:4444
kubectl port-forward svc/selenoid-ui 8080:8080

# ШАГ 2: поднятие сервисов мониторинга
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
helm repo add elastic https://helm.elastic.co || true
helm repo update

# Если упадёт с "no matches for kind ServiceMonitor ... ensure CRDs are installed first" —
# это известная гонка чарта: CRD ставятся, но не видны в том же запуске. Просто запусти команду ещё раз.
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack --version 86.1.0 -n monitoring --create-namespace -f monitoring-values.yaml

# Пробрасываем порт к прометеусу и графане
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 3001:9090 # > /dev/null 2>&1
kubectl port-forward svc/monitoring-grafana -n monitoring 3002:80

# Создаем секреты для авторизации на бекенде
kubectl create secret generic backend-basic-auth --from-literal=username=admin --from-literal=password=admin -n monitoring

# Применяем yaml с настройкой SpringMonitoring за бекендом
kubectl apply -f spring-monitoring.yaml

# ШАГ 3: поднятие логирования (Elasticsearch + Kibana + Filebeat)
# elastic репозиторий уже добавлен выше (helm repo add elastic ...)

# Elasticsearch — хранилище логов. Pin версии чарта 7.17.3 (single-node, без security)
helm upgrade --install elasticsearch elastic/elasticsearch --version 7.17.3 \
  -n logging --create-namespace -f elasticsearch-values.yaml

# Ждём, пока под(ы) Elasticsearch будут готовы, прежде чем ставить Kibana
kubectl rollout status statefulset/elasticsearch-master -n logging --timeout=300s

# Kibana — UI для просмотра логов
helm upgrade --install kibana elastic/kibana --version 7.17.3 \
  -n logging -f kibana-values.yaml

# Filebeat — DaemonSet, читает логи контейнеров и отправляет их в Elasticsearch.
# Именно он обеспечивает отправку логов приложения (backend) в Elasticsearch:
# подхватывает аннотации co.elastic.logs/* с пода backend (см. nbank-chart/templates/backend.yaml).
helm upgrade --install filebeat elastic/filebeat --version 7.17.3 \
  -n logging -f filebeat-values.yaml

# Проверяем, что всё поднялось
kubectl get pods -n logging

# Пробрасываем порт к Kibana (UI логов будет доступен на http://localhost:5601)
kubectl port-forward svc/kibana-kibana -n logging 5601:5601 # > /dev/null 2>&1 &

# (опционально) Проброс самого Elasticsearch для отладки / curl-запросов
# kubectl port-forward svc/elasticsearch-master -n logging 9200:9200

# Как убедиться, что логи приходят:
#   1) Открыть Kibana -> http://localhost:5601
#   2) Stack Management -> Index Patterns -> создать паттерн "filebeat-*" (поле времени @timestamp)
#   3) Discover -> отфильтровать по kubernetes.labels.app : backend
#   curl-проверка наличия индексов (нужен проброс 9200):
#   curl http://localhost:9200/_cat/indices/filebeat-*?v