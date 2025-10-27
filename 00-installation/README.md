# 🚀 RabbitMQ Installation Exercises

This section covers different ways to set up RabbitMQ for development, testing, and production environments.

## 📋 Exercise Overview

| Exercise | Description | Environment | Complexity |
|----------|-------------|-------------|------------|
| [ex01](ex01/) | Single Docker Container | Local Development | ⭐ |
| [ex02](ex02/) | Docker Compose Cluster | Local Testing/Staging | ⭐⭐⭐ |
| [ex03](ex03/) | Kubernetes Operator | Production/Killercoda | ⭐⭐⭐⭐ |

## 🎯 Learning Objectives

After completing these exercises, you will understand:

- **Single Instance Setup**: Quick development environment
- **Cluster Configuration**: High availability and load distribution
- **Container Orchestration**: Production-ready deployments
- **Monitoring and Management**: Health checks and observability
- **Scaling Operations**: Adding/removing nodes
- **Troubleshooting**: Common issues and solutions

## 🛠️ Prerequisites

### General Requirements
- Basic understanding of RabbitMQ concepts
- Command line familiarity
- Text editor or IDE

### Exercise-Specific Requirements

#### Exercise 1 (Docker)
- Docker installed and running
- 2GB available RAM
- Ports 5672, 15672 available

#### Exercise 2 (Docker Compose)
- Docker and Docker Compose
- 4GB available RAM
- Ports 5671-5674, 15672-15674, 8080 available

#### Exercise 3 (Kubernetes)
- Kubernetes cluster (local or Killercoda)
- kubectl configured
- Basic Kubernetes knowledge

## 🚀 Quick Start

### Choose Your Path

**🏃‍♂️ Just want to get started quickly?**
```bash
cd ex01
./docker-run.sh
```

**🏗️ Need a production-like cluster?**
```bash
cd ex02
docker-compose up -d
python test_cluster.py
```

**☸️ Working with Kubernetes?**
```bash
cd ex03
./killercoda-setup.sh
```

## 📊 Comparison Matrix

| Feature | Single Docker | Docker Compose | Kubernetes |
|---------|---------------|----------------|------------|
| **Setup Time** | < 2 minutes | < 5 minutes | < 10 minutes |
| **High Availability** | ❌ | ✅ | ✅ |
| **Load Balancing** | ❌ | ✅ (HAProxy) | ✅ (Native) |
| **Auto Scaling** | ❌ | Manual | ✅ |
| **Production Ready** | ❌ | Partial | ✅ |
| **Resource Usage** | Low | Medium | Medium-High |
| **Complexity** | Simple | Moderate | Advanced |

## 🔍 What You'll Learn

### Exercise 1: Foundation
- Basic RabbitMQ container setup
- Management UI navigation
- Connection testing
- Basic monitoring

### Exercise 2: Clustering
- Multi-node cluster formation
- High availability configuration
- Load balancer setup
- Failover testing
- Performance monitoring

### Exercise 3: Production
- Kubernetes operator usage
- Custom resource definitions
- Persistent storage
- Service discovery
- Scaling operations
- Production monitoring

## 🎓 Progression Path

1. **Start with Exercise 1** - Get familiar with RabbitMQ basics
2. **Move to Exercise 2** - Understand clustering and HA
3. **Advance to Exercise 3** - Learn production deployment

Each exercise builds upon the previous one, introducing more complex concepts and production considerations.

## 🔧 Common Commands

### Health Checks
```bash
# Docker
docker exec <container> rabbitmqctl status

# Kubernetes
kubectl exec <pod> -- rabbitmqctl status
```

### Cluster Status
```bash
# Docker
docker exec <container> rabbitmqctl cluster_status

# Kubernetes  
kubectl exec <pod> -- rabbitmqctl cluster_status
```

### Queue Management
```bash
# List queues
rabbitmqctl list_queues

# List exchanges
rabbitmqctl list_exchanges

# List bindings
rabbitmqctl list_bindings
```

## 🆘 Troubleshooting

### Common Issues

**Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep :5672
lsof -i :15672
```

**Memory Issues**
```bash
# Check container memory
docker stats
kubectl top pods
```

**Network Connectivity**
```bash
# Test connectivity
telnet localhost 5672
curl http://localhost:15672
```

### Getting Help

1. Check the specific exercise README
2. Review container/pod logs
3. Verify network connectivity
4. Check resource availability
5. Consult RabbitMQ documentation

## 📚 Additional Resources

- [RabbitMQ Official Documentation](https://www.rabbitmq.com/documentation.html)
- [Docker Hub - RabbitMQ](https://hub.docker.com/_/rabbitmq)
- [RabbitMQ Cluster Operator](https://github.com/rabbitmq/cluster-operator)
- [Killercoda Kubernetes Playground](https://killercoda.com/kubernetes)

## 🎯 Next Steps

After completing the installation exercises, proceed to:
- [01-basics](../01-basics/) - Fundamental RabbitMQ concepts
- [02-direct-exchange](../02-direct-exchange/) - Message routing patterns
- [03-fanout-exchange](../03-fanout-exchange/) - Broadcasting patterns