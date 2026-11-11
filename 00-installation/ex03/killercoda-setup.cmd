@echo off

REM RabbitMQ Kubernetes Setup Script for Killercoda

echo 🐇 RabbitMQ Kubernetes Setup for Killercoda
echo ============================================

REM Check if kubectl is available
kubectl version --client >nul 2>&1
if errorlevel 1 (
    echo [ERROR] kubectl is not installed or not in PATH
    exit /b 1
)

REM Check cluster connectivity
echo [INFO] Checking Kubernetes cluster connectivity...
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Cannot connect to Kubernetes cluster
    exit /b 1
)
echo [SUCCESS] Connected to Kubernetes cluster

REM Show cluster info
echo [INFO] Cluster information:
kubectl cluster-info
echo.

REM Install cert-manager (required by the Cluster Operator 2.20+ for its webhook certificate)
echo [INFO] Installing cert-manager...
kubectl apply -f "https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml"
kubectl wait --for=condition=Available deployment --all -n cert-manager --timeout=300s

REM Install RabbitMQ Cluster Operator
echo [INFO] Installing RabbitMQ Cluster Operator...
kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"

echo [INFO] Waiting for operator to be ready...
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=rabbitmq-cluster-operator -n rabbitmq-system --timeout=300s

echo [SUCCESS] RabbitMQ Cluster Operator installed successfully

REM Deploy RabbitMQ cluster
echo [INFO] Deploying RabbitMQ cluster...
kubectl apply -f rabbitmq-cluster.yaml

echo [INFO] Waiting for RabbitMQ cluster to be ready...
kubectl wait --for=condition=AllReplicasReady rabbitmqcluster/rabbitmq-cluster --timeout=600s

echo [SUCCESS] RabbitMQ cluster deployed successfully

REM Deploy test pod
echo [INFO] Deploying test pod...
kubectl apply -f test-pod.yaml

kubectl wait --for=condition=Ready pod/rabbitmq-test --timeout=120s

echo [SUCCESS] Setup completed!
echo.
echo Management UI: http://localhost:15672
echo Username: admin
echo Password: killercoda123