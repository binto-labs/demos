# Earthquake Claim Accelerator - System Architecture Document

## Document Information
- **Version**: 1.0.0
- **Date**: 2025-08-27
- **Status**: Final
- **Prepared By**: System Architecture Designer

---

## Table of Contents

1. [High-Level Architecture Overview](#1-high-level-architecture-overview)
2. [Component Architecture](#2-component-architecture)
3. [Infrastructure Design](#3-infrastructure-design)
4. [Data Architecture](#4-data-architecture)
5. [Security Architecture](#5-security-architecture)
6. [Integration Points](#6-integration-points)
7. [Scalability Design](#7-scalability-design)

---

## 1. High-Level Architecture Overview

### 1.1 System Context

```mermaid
graph TB
    subgraph "External Users"
        CM[Claims Manager]
        PO[Property Owner]
        LC[Legal Counsel]
        IA[Insurance Adjuster]
    end

    subgraph "External Services"
        OPENAI[OpenAI API]
        GEONET[GeoNet API]
        EMAIL[Email Service]
        STORAGE[File Storage]
    end

    subgraph "Earthquake Claim Accelerator System"
        WEB[Web Application]
        API[API Gateway]
        BACKEND[Backend Services]
        DB[(Database)]
        CACHE[(Cache)]
    end

    CM --> WEB
    PO --> WEB
    LC --> WEB
    IA --> WEB

    WEB --> API
    API --> BACKEND
    BACKEND --> DB
    BACKEND --> CACHE
    BACKEND --> OPENAI
    BACKEND --> GEONET
    BACKEND --> EMAIL
    BACKEND --> STORAGE
```

### 1.2 Solution Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        NEXTJS[Next.js Application]
        COMPONENTS[React Components]
        STATE[State Management]
    end

    subgraph "API Layer"
        KONG[Kong API Gateway]
        AUTH[Authentication]
        RATE[Rate Limiting]
    end

    subgraph "Business Logic Layer"
        CLAIM[Claim Service]
        DOC[Document Service]
        PREC[Precedent Service]
        AI[AI Analysis Service]
        NOTIF[Notification Service]
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL + pgvector)]
        REDIS[(Redis Cache)]
        MINIO[(MinIO Object Storage)]
    end

    subgraph "Processing Layer"
        CELERY[Celery Workers]
        QUEUE[Task Queue]
    end

    NEXTJS --> KONG
    KONG --> CLAIM
    KONG --> DOC
    KONG --> PREC
    KONG --> AI

    CLAIM --> POSTGRES
    DOC --> POSTGRES
    PREC --> POSTGRES
    AI --> POSTGRES

    DOC --> CELERY
    AI --> CELERY
    CELERY --> QUEUE
    QUEUE --> REDIS

    DOC --> MINIO
    CLAIM --> MINIO

    CLAIM --> REDIS
    PREC --> REDIS
```

### 1.3 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14, React 18, TypeScript | Modern web application framework |
| API Gateway | Kong | Request routing, authentication, rate limiting |
| Backend | Python 3.10+, FastAPI | High-performance API services |
| Database | PostgreSQL 14+ with pgvector | Relational data with vector similarity search |
| Cache | Redis 6.0+ | Session management and performance optimization |
| Storage | MinIO | S3-compatible object storage |
| Processing | Celery | Asynchronous task processing |
| AI/ML | OpenAI GPT-4 | Document analysis and text generation |
| Monitoring | Prometheus, Grafana | Application and infrastructure monitoring |

---

## 2. Component Architecture

### 2.1 Frontend Components

```mermaid
graph TB
    subgraph "Next.js Application"
        PAGES[Pages/Routes]
        LAYOUTS[Layout Components]
        
        subgraph "Feature Components"
            PROP[Property Management]
            CLAIM[Claim Processing]
            DOC_UP[Document Upload]
            PREC_VIEW[Precedent Viewer]
            PKG[Package Generator]
        end
        
        subgraph "Shared Components"
            UI[UI Components]
            FORMS[Form Components]
            CHARTS[Data Visualization]
            FILE[File Upload]
        end
        
        subgraph "State Management"
            QUERY[React Query]
            CONTEXT[React Context]
            HOOKS[Custom Hooks]
        end
        
        subgraph "Services"
            API_CLIENT[API Client]
            WS[WebSocket Client]
            UTILS[Utilities]
        end
    end

    PAGES --> LAYOUTS
    LAYOUTS --> PROP
    LAYOUTS --> CLAIM
    LAYOUTS --> DOC_UP
    LAYOUTS --> PREC_VIEW
    LAYOUTS --> PKG

    PROP --> UI
    CLAIM --> FORMS
    DOC_UP --> FILE
    PREC_VIEW --> CHARTS
    PKG --> UI

    PROP --> QUERY
    CLAIM --> CONTEXT
    DOC_UP --> HOOKS

    QUERY --> API_CLIENT
    CONTEXT --> WS
    HOOKS --> UTILS
```

### 2.2 Backend Services Architecture

```mermaid
graph TB
    subgraph "API Gateway Layer"
        KONG[Kong Gateway]
        JWT[JWT Validation]
        CORS[CORS Handler]
        LIMIT[Rate Limiter]
    end

    subgraph "Core Services"
        subgraph "Claim Service"
            CLAIM_API[Claim API]
            CLAIM_LOGIC[Business Logic]
            CLAIM_MODEL[Data Models]
        end
        
        subgraph "Document Service"
            DOC_API[Document API]
            DOC_PROC[Processing Engine]
            DOC_STORE[Storage Manager]
        end
        
        subgraph "Precedent Service"
            PREC_API[Precedent API]
            VECTOR_SEARCH[Vector Search]
            MATCH_ENGINE[Matching Engine]
        end
        
        subgraph "AI Service"
            AI_API[AI API]
            TEXT_EXTRACT[Text Extraction]
            IMAGE_ANALYSIS[Image Analysis]
        end
    end

    subgraph "Worker Services"
        CELERY_WORKER[Celery Workers]
        PDF_WORKER[PDF Processor]
        IMAGE_WORKER[Image Processor]
        AI_WORKER[AI Processor]
    end

    KONG --> CLAIM_API
    KONG --> DOC_API
    KONG --> PREC_API
    KONG --> AI_API

    DOC_API --> CELERY_WORKER
    AI_API --> CELERY_WORKER

    CELERY_WORKER --> PDF_WORKER
    CELERY_WORKER --> IMAGE_WORKER
    CELERY_WORKER --> AI_WORKER
```

### 2.3 Data Processing Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant DocService
    participant Queue
    participant Worker
    participant AI
    participant Database
    participant Notification

    User->>Frontend: Upload PDF Report
    Frontend->>API: POST /documents/upload
    API->>DocService: Process Document
    DocService->>Queue: Queue Processing Job
    DocService->>Frontend: Return Job ID
    
    Queue->>Worker: Assign Processing Task
    Worker->>AI: Extract Text & Structure
    AI-->>Worker: Return Structured Data
    Worker->>Database: Save Extracted Data
    Worker->>Notification: Send Completion Event
    Notification->>Frontend: WebSocket Update
    Frontend->>User: Display Results
```

---

## 3. Infrastructure Design

### 3.1 Container Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[NGINX Load Balancer]
    end

    subgraph "Application Containers"
        subgraph "Frontend Pod"
            NEXT1[Next.js Instance 1]
            NEXT2[Next.js Instance 2]
        end
        
        subgraph "API Pod"
            API1[FastAPI Instance 1]
            API2[FastAPI Instance 2]
        end
        
        subgraph "Worker Pod"
            WORKER1[Celery Worker 1]
            WORKER2[Celery Worker 2]
            WORKER3[Celery Worker 3]
        end
    end

    subgraph "Data Services"
        POSTGRES[(PostgreSQL Primary)]
        POSTGRES_READ[(PostgreSQL Read Replica)]
        REDIS[(Redis Cluster)]
        MINIO[(MinIO Cluster)]
    end

    LB --> NEXT1
    LB --> NEXT2
    NEXT1 --> API1
    NEXT2 --> API2
    
    API1 --> POSTGRES
    API2 --> POSTGRES
    API1 --> POSTGRES_READ
    API2 --> POSTGRES_READ
    
    WORKER1 --> REDIS
    WORKER2 --> REDIS
    WORKER3 --> REDIS
    
    API1 --> MINIO
    API2 --> MINIO
    WORKER1 --> MINIO
```

### 3.2 Kubernetes Deployment

```yaml
# Key Kubernetes Resources
apiVersion: v1
kind: Namespace
metadata:
  name: earthquake-claims

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  namespace: earthquake-claims
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    spec:
      containers:
      - name: backend
        image: earthquake-claims/backend:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### 3.3 Docker Compose (Development)

```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg14
    environment:
      POSTGRES_DB: earthquake_claims
      POSTGRES_USER: claims_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://claims_user:secure_password@postgres/earthquake_claims
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

---

## 4. Data Architecture

### 4.1 Database Design

```mermaid
erDiagram
    PROPERTY ||--o{ INSURANCE_POLICY : has
    PROPERTY ||--o{ CLAIM : related_to
    EARTHQUAKE_EVENT ||--o{ CLAIM : triggers
    INSURANCE_POLICY ||--o{ CLAIM : covers
    CLAIM ||--o{ DAMAGE_ASSESSMENT : includes
    CLAIM ||--o{ CLAIM_DOCUMENT : contains
    PRECEDENT_CASE }o--o{ CLAIM : similar_to

    PROPERTY {
        uuid id PK
        text address
        varchar building_type
        integer floors
        integer year_built
        decimal nbs_rating
        decimal valuation
        timestamp created_at
    }

    INSURANCE_POLICY {
        uuid id PK
        uuid property_id FK
        varchar insurer
        varchar policy_number
        decimal sum_insured
        decimal nhc_cover
        date renewal_date
    }

    CLAIM {
        uuid id PK
        uuid property_id FK
        uuid event_id FK
        varchar status
        decimal claimed_amount
        decimal nhc_portion
        decimal private_portion
        timestamp created_at
    }

    PRECEDENT_CASE {
        uuid id PK
        varchar case_reference
        varchar building_type
        decimal claim_amount
        decimal settlement_amount
        text_array key_arguments
        vector embedding
    }
```

### 4.2 Data Flow Architecture

```mermaid
flowchart TD
    subgraph "Data Sources"
        USER[User Input]
        PDF[PDF Documents]
        IMAGES[Damage Photos]
        EXT_API[External APIs]
    end

    subgraph "Data Processing"
        VALIDATION[Data Validation]
        EXTRACTION[AI Extraction]
        ENHANCEMENT[Data Enhancement]
        EMBEDDING[Vector Embedding]
    end

    subgraph "Data Storage"
        POSTGRES[(PostgreSQL)]
        VECTORS[(Vector Store)]
        FILES[(File Storage)]
        CACHE[(Cache Layer)]
    end

    subgraph "Data Access"
        API_LAYER[API Layer]
        QUERY_OPT[Query Optimization]
        CACHING[Caching Strategy]
    end

    USER --> VALIDATION
    PDF --> EXTRACTION
    IMAGES --> EXTRACTION
    EXT_API --> ENHANCEMENT

    VALIDATION --> POSTGRES
    EXTRACTION --> EMBEDDING
    ENHANCEMENT --> POSTGRES
    EMBEDDING --> VECTORS

    POSTGRES --> API_LAYER
    VECTORS --> QUERY_OPT
    FILES --> CACHING
    CACHE --> API_LAYER
```

### 4.3 Vector Search Implementation

```sql
-- Create vector extension and indexes
CREATE EXTENSION IF NOT EXISTS vector;

-- Precedent cases with embeddings
CREATE TABLE precedent_cases (
    id UUID PRIMARY KEY,
    case_reference VARCHAR(50),
    building_type VARCHAR(20),
    case_summary TEXT,
    embedding vector(1536) -- OpenAI embedding size
);

-- Create vector similarity index
CREATE INDEX idx_precedent_embedding 
ON precedent_cases 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Example similarity search query
SELECT 
    id, case_reference, building_type,
    1 - (embedding <-> $1) as similarity
FROM precedent_cases 
WHERE building_type = $2
ORDER BY embedding <-> $1 
LIMIT 10;
```

---

## 5. Security Architecture

### 5.1 Security Layers

```mermaid
graph TB
    subgraph "Perimeter Security"
        WAF[Web Application Firewall]
        DDoS[DDoS Protection]
        SSL[SSL/TLS Termination]
    end

    subgraph "Application Security"
        AUTH[Authentication]
        AUTHZ[Authorization]
        SESSION[Session Management]
        CSRF[CSRF Protection]
    end

    subgraph "API Security"
        JWT[JWT Tokens]
        RATE_LIMIT[Rate Limiting]
        INPUT_VAL[Input Validation]
        AUDIT[Audit Logging]
    end

    subgraph "Data Security"
        ENCRYPT_REST[Encryption at Rest]
        ENCRYPT_TRANSIT[Encryption in Transit]
        DATA_MASK[Data Masking]
        BACKUP_ENC[Backup Encryption]
    end

    subgraph "Infrastructure Security"
        NETWORK[Network Segmentation]
        SECRETS[Secrets Management]
        MONITORING[Security Monitoring]
        COMPLIANCE[Compliance Controls]
    end

    WAF --> AUTH
    AUTH --> JWT
    JWT --> ENCRYPT_REST
    ENCRYPT_REST --> NETWORK
```

### 5.2 Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API_Gateway
    participant Auth_Service
    participant Backend
    participant Database

    User->>Frontend: Login Request
    Frontend->>API_Gateway: POST /auth/login
    API_Gateway->>Auth_Service: Validate Credentials
    Auth_Service->>Database: Check User
    Database-->>Auth_Service: User Data
    Auth_Service-->>API_Gateway: JWT Token
    API_Gateway-->>Frontend: Token + User Info
    Frontend-->>User: Login Success

    Note over Frontend: Store JWT securely
    
    User->>Frontend: Access Protected Resource
    Frontend->>API_Gateway: Request + JWT Header
    API_Gateway->>Auth_Service: Validate JWT
    Auth_Service-->>API_Gateway: Token Valid
    API_Gateway->>Backend: Forward Request
    Backend-->>API_Gateway: Response
    API_Gateway-->>Frontend: Protected Data
```

### 5.3 Data Protection

| Security Control | Implementation | Purpose |
|------------------|----------------|---------|
| Encryption at Rest | AES-256 | Protect stored data |
| Encryption in Transit | TLS 1.3 | Secure data transmission |
| Key Management | HSM/Vault | Secure key storage |
| Data Masking | PII anonymization | Protect sensitive data |
| Access Control | RBAC | Limit data access |
| Audit Logging | Comprehensive logging | Compliance and monitoring |

---

## 6. Integration Points

### 6.1 External Integrations

```mermaid
graph LR
    subgraph "Earthquake Claim System"
        CORE[Core System]
    end

    subgraph "AI/ML Services"
        OPENAI[OpenAI GPT-4]
        VISION[Vision Models]
        EMBEDDING[Embedding Service]
    end

    subgraph "Government Data"
        GEONET[GeoNet API]
        LINZ[LINZ Property Data]
        BUILDING[Building Consent]
    end

    subgraph "Business Services"
        EMAIL[Email Service]
        SMS[SMS Service]
        STORAGE[Cloud Storage]
    end

    subgraph "Future Integrations"
        ERP[ERP Systems]
        INSURANCE[Insurer APIs]
        LEGAL[Legal Databases]
    end

    CORE --> OPENAI
    CORE --> VISION
    CORE --> EMBEDDING
    CORE --> GEONET
    CORE --> LINZ
    CORE --> EMAIL
    CORE --> STORAGE
    
    CORE -.-> ERP
    CORE -.-> INSURANCE
    CORE -.-> LEGAL
```

### 6.2 API Integration Architecture

```yaml
# API Integration Specifications
integrations:
  openai:
    base_url: "https://api.openai.com/v1"
    authentication: "Bearer Token"
    rate_limits:
      requests_per_minute: 3000
      tokens_per_minute: 250000
    retry_policy:
      max_attempts: 3
      backoff_strategy: "exponential"
    
  geonet:
    base_url: "https://api.geonet.org.nz"
    authentication: "None"
    rate_limits:
      requests_per_hour: 1000
    cache_ttl: 3600
    
  email:
    provider: "SendGrid"
    authentication: "API Key"
    templates:
      - claim_created
      - processing_complete
      - package_ready
```

---

## 7. Scalability Design

### 7.1 Horizontal Scaling Strategy

```mermaid
graph TB
    subgraph "Load Balancing"
        ALB[Application Load Balancer]
        HEALTH[Health Check]
    end

    subgraph "Auto Scaling Groups"
        subgraph "Frontend Tier"
            FE1[Frontend Instance 1]
            FE2[Frontend Instance 2]
            FE3[Frontend Instance N]
        end
        
        subgraph "API Tier"
            API1[API Instance 1]
            API2[API Instance 2]
            API3[API Instance N]
        end
        
        subgraph "Worker Tier"
            W1[Worker Instance 1]
            W2[Worker Instance 2]
            W3[Worker Instance N]
        end
    end

    subgraph "Data Tier"
        PG_MASTER[(PostgreSQL Master)]
        PG_REPLICA[(PostgreSQL Replicas)]
        REDIS_CLUSTER[(Redis Cluster)]
    end

    ALB --> FE1
    ALB --> FE2
    ALB --> FE3
    
    FE1 --> API1
    FE2 --> API2
    FE3 --> API3
    
    API1 --> PG_MASTER
    API2 --> PG_REPLICA
    API3 --> PG_REPLICA
    
    W1 --> REDIS_CLUSTER
    W2 --> REDIS_CLUSTER
    W3 --> REDIS_CLUSTER
```

### 7.2 Performance Optimization

| Component | Optimization Strategy | Target Metric |
|-----------|----------------------|---------------|
| Database | Read replicas, connection pooling | <200ms query time |
| Cache | Redis clustering, cache warming | 95% cache hit rate |
| API | Response compression, pagination | <500ms response time |
| Frontend | Code splitting, CDN | <3s page load |
| Workers | Queue optimization, parallel processing | <5min document processing |

### 7.3 Monitoring & Observability

```yaml
monitoring_stack:
  metrics:
    - prometheus: "System and application metrics"
    - grafana: "Visualization and alerting"
    - node_exporter: "Infrastructure metrics"
    
  logging:
    - elasticsearch: "Centralized logging"
    - logstash: "Log processing"
    - kibana: "Log visualization"
    
  tracing:
    - jaeger: "Distributed tracing"
    - opentelemetry: "Instrumentation"
    
  alerting:
    - prometheus_alertmanager: "Alert routing"
    - pagerduty: "Incident management"
    - slack: "Team notifications"

key_metrics:
  availability: "99.5% uptime SLA"
  response_time: "95th percentile < 500ms"
  throughput: "1000 requests/minute peak"
  error_rate: "< 0.1% error rate"
  document_processing: "< 5 minutes completion time"
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Database Technology Selection
- **Decision**: PostgreSQL with pgvector extension
- **Rationale**: Combines relational data management with vector similarity search
- **Consequences**: Single database technology reduces complexity, pgvector provides native vector operations

### ADR-002: Frontend Framework Choice
- **Decision**: Next.js 14 with App Router
- **Rationale**: Modern React framework with built-in SSR, routing, and optimization
- **Consequences**: Strong TypeScript support, excellent developer experience, SEO benefits

### ADR-003: API Architecture Pattern
- **Decision**: Microservices with API Gateway
- **Rationale**: Enables independent scaling, technology diversity, and team autonomy
- **Consequences**: Increased complexity but better scalability and maintainability

### ADR-004: AI Integration Strategy
- **Decision**: OpenAI API with fallback mechanisms
- **Rationale**: Proven accuracy for document processing, rapid development
- **Consequences**: External dependency requires robust error handling and cost management

---

## Quality Attributes

| Quality Attribute | Requirement | Architectural Support |
|------------------|-------------|----------------------|
| **Performance** | <2s response time | Caching, CDN, database optimization |
| **Scalability** | 100+ concurrent users | Horizontal scaling, load balancing |
| **Availability** | 99.5% uptime | Redundancy, health checks, failover |
| **Security** | Enterprise-grade | Multi-layer security, encryption, RBAC |
| **Maintainability** | Modular codebase | Microservices, clean architecture |
| **Usability** | Intuitive interface | User-centered design, responsive UI |

---

## Deployment Strategy

### MVP Deployment (Months 1-3)
- Single-region deployment
- 2-3 service instances per component
- Basic monitoring and alerting
- Manual deployment process

### Production Deployment (Months 4-6)
- Multi-AZ deployment
- Auto-scaling groups
- Comprehensive monitoring
- CI/CD pipeline automation

### Scale-Out Deployment (Months 7+)
- Multi-region deployment
- Advanced monitoring and observability
- Blue-green deployment strategy
- Disaster recovery procedures

---

*This system architecture document provides the technical foundation for building a scalable, secure, and maintainable earthquake claim accelerator platform. All implementation work should align with the architectural decisions and patterns outlined in this document.*