terraform {
  required_version = ">= 1.6.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.31"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

variable "kubeconfig_path" {
  type        = string
  description = "Path to kubeconfig for the local cluster."
  default     = "~/.kube/config"
}

variable "namespaces" {
  type    = set(string)
  default = ["risk-assistant", "platform", "kafka", "observability", "cicd"]
}

resource "kubernetes_namespace" "base" {
  for_each = var.namespaces

  metadata {
    name = each.value
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "istio-injection"              = each.value == "risk-assistant" ? "enabled" : "disabled"
    }
  }
}

resource "kubernetes_service_account" "risk_assistant" {
  metadata {
    name      = "risk-assistant"
    namespace = kubernetes_namespace.base["risk-assistant"].metadata[0].name
    labels = {
      "app.kubernetes.io/part-of" = "risk-assistant"
    }
  }
}

resource "kubernetes_secret" "risk_assistant_config" {
  metadata {
    name      = "risk-assistant-config"
    namespace = kubernetes_namespace.base["risk-assistant"].metadata[0].name
  }

  data = {
    POSTGRES_DSN            = "postgresql://risk_user:risk_password@postgresql.risk-assistant.svc.cluster.local:5432/risk_assistant"
    MONGO_URI               = "mongodb://mongodb.risk-assistant.svc.cluster.local:27017"
    REDIS_URL               = "redis://valkey.risk-assistant.svc.cluster.local:6379/0"
    KAFKA_BOOTSTRAP_SERVERS = "risk-kafka-bootstrap.kafka.svc.cluster.local:9092"
  }

  type = "Opaque"
}

