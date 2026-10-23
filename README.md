# CloudPulse

> Distributed service monitoring platform for detecting slowdowns, failures, and service recovery in real time.

CloudPulse is a Dockerized full-stack monitoring platform that continuously checks HTTP services, classifies their health, manages alerts, stores monitoring history, and streams live status updates to a React dashboard.

## Problem

Teams often discover service outages through users instead of monitoring systems. Manual health checks do not scale, and without historical monitoring data it is difficult to understand service degradation, failures, and recovery patterns.

CloudPulse addresses this by automatically monitoring services, detecting failures, managing alerts, and providing real-time visibility through a centralized dashboard.

## Monitoring Flow

```text
Schedule Checks
      ↓
Probe Services
      ↓
Classify Health
      ↓
Store Results
      ↓
Manage Alerts
      ↓
Publish Events
      ↓
Stream Live Updates
      ↓
React Dashboard
Key Features
- Automated scheduled HTTP health checks using Celery and Celery Beat
- Service health classification: UP, DEGRADED, and DOWN
- Failure detection using consecutive failed checks
- Warning and critical alert management
- Alert escalation and recovery tracking
- Real-time dashboard updates using WebSockets
- Redis Pub/Sub for event distribution
- PostgreSQL for monitoring history and application data
- Redis caching for dashboard statistics
- JWT-based authentication
- Admin and viewer role-based access control
- Login rate limiting
- Service search, filtering, pagination, and response-time history
- Dockerized development and deployment environment
- REST APIs with FastAPI
- Automated backend tests with Pytest
Alert Lifecycle
UP
 ↓
DEGRADED
 ↓
DOWN
 ↓
CRITICAL ALERT
 ↓
SERVICE RECOVERS
 ↓
ALERT RESOLVED

CloudPulse maintains an active alert for an unhealthy service and escalates warning alerts when the service progresses to a critical state. When the service recovers, the active alert is automatically resolved.
System Architecture
                    ┌─────────────────────┐
                    │     React Frontend   │
                    │      Dashboard       │
                    └──────────┬──────────┘
                               │
                         REST / WebSocket
                               │
                    ┌──────────▼──────────┐
                    │     FastAPI API     │
                    │ Authentication/RBAC │
                    └──────┬───────┬──────┘
                           │       │
                 ┌─────────▼─┐   ┌─▼──────────┐
                 │ PostgreSQL │   │   Redis    │
                 │   Data     │   │ Cache/PubSub│
                 └────────────┘   └─────┬──────┘
                                        │
                                  ┌─────▼─────┐
                                  │  Celery   │
                                  │  Worker   │
                                  └─────┬─────┘
                                        │
                                  ┌─────▼─────┐
                                  │ Celery     │
                                  │ Beat       │
                                  └─────┬─────┘
                                        │
                                  HTTP Health
                                     Checks
                                        │
                           ┌────────────▼────────────┐
                           │    Monitored Services   │
                           └─────────────────────────┘

Technology Stack
Layer	Technologies
Frontend	React, JavaScript
Backend	Python, FastAPI
API	REST APIs, WebSockets
Database	PostgreSQL
ORM	SQLAlchemy
Async Processing	Celery, Celery Beat
Cache & Messaging	Redis, Redis Pub/Sub
Authentication	JWT, bcrypt
HTTP Monitoring	HTTPX
Containerization	Docker, Docker Compose
Testing	Pytest
Version Control	Git, GitHub


Project Structure
CloudPulse/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── tasks/
│   │   ├── main.py
│   │   └── ...
│   │
│   └── tests/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── ...
│
├── docs/
│   ├── dashboard.png
│   ├── services.png
│   └── alerts.png
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md

API Endpoints
Authentication
Method	Endpoint	Purpose
POST	/api/auth/register	Register a user
POST	/api/auth/login	Authenticate user
GET	/api/auth/me	Get current user


Services
Method	Endpoint	Purpose
GET	/api/services	List monitored services
POST	/api/services	Create a monitored service
GET	/api/services/{service_id}	Get service details
GET	/api/services/{service_id}/results	Get monitoring history


Alerts
Method	Endpoint	Purpose
GET	/api/alerts	List alerts
POST	/api/alerts/{alert_id}/acknowledge	Acknowledge an alert


Dashboard
Method	Endpoint	Purpose
GET	/api/dashboard/summary	Get dashboard statistics


Demo Services
Endpoint	Purpose
/api/demo/ok	Simulates a healthy service
/api/demo/slow	Simulates a slow service
/api/demo/flaky	Simulates intermittent failures
/api/demo/down	Simulates a failed service
/api/health	Application health check


Demo Scenario
CloudPulse can demonstrate a complete service incident lifecycle:
Healthy Service
      ↓
Slow Response
      ↓
DEGRADED
      ↓
Repeated Failures
      ↓
DOWN
      ↓
CRITICAL ALERT
      ↓
Service Recovers
      ↓
UP
      ↓
ALERT RESOLVED

Screenshots
Dashboard

Services

Alerts

Getting Started
Prerequisites
Make sure the following are installed:
- Docker
- Docker Compose
- Git
Clone the Repository
git clone https://github.com/prerna354/CloudPulse.git
cd CloudPulse

Configure Environment Variables
Create a .env file using .env.example as a reference.
cp .env.example .env

Update the environment variables with appropriate local values.
Start the Application
docker compose up --build

The application services include:
- React frontend
- FastAPI backend
- PostgreSQL database
- Redis
- Celery worker
- Celery Beat
Testing
Backend tests can be executed using:
docker compose exec backend pytest

Development Highlights
CloudPulse demonstrates practical software engineering concepts including:
- REST API design
- Real-time communication
- Background task processing
- Scheduled jobs
- Database persistence
- Caching
- Publish/subscribe messaging
- Authentication and authorization
- Failure detection
- Alert lifecycle management
- Containerized application architecture
- Automated testing
- Git-based version control
Future Improvements
Potential future enhancements include:
- Email and Slack alert notifications
- Advanced monitoring metrics
- Service dependency mapping
- Distributed tracing
- More detailed observability dashboards
- Kubernetes deployment
- Prometheus and Grafana integration
License
MIT License.