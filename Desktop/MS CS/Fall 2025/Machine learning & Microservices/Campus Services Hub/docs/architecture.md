# Campus Services Hub - Architecture Documentation

## System Architecture

The Campus Services Hub is built using a microservices architecture pattern, with each service responsible for a specific domain of functionality.

## Architecture Diagram

```
                                    USERS
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │   CloudFront (CDN)      │
                        │   Content Delivery      │
                        └────────────┬────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │   S3 Bucket             │
                        │   React Frontend        │
                        │   (Static Hosting)      │
                        └────────────┬────────────┘
                                     │
                                     │ HTTPS
                                     ▼
                        ┌─────────────────────────┐
                        │ Application Load        │
                        │ Balancer (ALB)          │
                        └────────────┬────────────┘
                                     │
                                     │ HTTP
                                     ▼
                        ┌─────────────────────────┐
                        │   API Gateway           │
                        │   Port: 3000            │
                        │   - Request Routing     │
                        │   - Correlation IDs     │
                        │   - Health Aggregation  │
                        └──┬──┬──┬──┬─────────────┘
                           │  │  │  │
        ┌──────────────────┘  │  │  └──────────────────┐
        │                     │  │                     │
        │                     │  └──────────┐          │
        │                     │             │          │
        ▼                     ▼             ▼          ▼
┌───────────────┐   ┌───────────────┐ ┌──────────┐ ┌──────────────┐
│ User Service  │   │Ticket Service │ │ Booking  │ │Notification  │
│   Port: 3001  │   │  Port: 3002   │ │ Service  │ │   Service    │
│               │   │               │ │Port: 3003│ │  Port: 3004  │
│ - Auth        │   │ - CRUD Ops    │ │          │ │              │
│ - JWT Tokens  │   │ - Status Mgmt │ │ - Rooms  │ │ - Delivery   │
│ - Profiles    │   │ - Priorities  │ │ - Avail. │ │ - Read/Unread│
│ - RBAC        │   │ - Categories  │ │ - Booking│ │ - Types      │
└───────┬───────┘   └───────┬───────┘ └────┬─────┘ └──────┬───────┘
        │                   │              │              │
        │                   │              │              │
        ▼                   ▼              ▼              ▼
┌───────────────┐   ┌───────────────┐ ┌──────────┐ ┌──────────────┐
│  PostgreSQL   │   │  PostgreSQL   │ │PostgreSQL│ │   MongoDB    │
│   user_db     │   │   ticket_db   │ │booking_db│ │notification_ │
│               │   │               │ │          │ │     db       │
│ - users       │   │ - tickets     │ │ - rooms  │ │- notifications│
│               │   │               │ │ - bookings│ │              │
└───────────────┘   └───────────────┘ └──────────┘ └──────────────┘
```

## Service Communication Flow

### User Registration & Login
```
Frontend → API Gateway → User Service → PostgreSQL
                              ↓
                         JWT Token
                              ↓
                          Frontend
```

### Creating a Ticket
```
Frontend → API Gateway → Ticket Service → PostgreSQL
                              ↓
                         Notification Service → MongoDB
                              ↓
                          Frontend (notification badge)
```

### Booking a Room
```
Frontend → API Gateway → Booking Service → PostgreSQL
                              ↓                (check conflicts)
                         Notification Service → MongoDB
                              ↓
                          Frontend (confirmation)
```

## Technology Stack

### Backend Services
- **Runtime**: Node.js 18
- **Framework**: Express.js
- **Authentication**: JWT (jsonwebtoken)
- **Password Hashing**: bcrypt
- **Databases**: 
  - PostgreSQL 15 (user, ticket, booking)
  - MongoDB 7 (notifications)
- **HTTP Client**: axios (inter-service communication)

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **State Management**: React Query (TanStack Query)
- **HTTP Client**: axios

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose (local), AWS ECS Fargate (production)
- **CI/CD**: GitHub Actions
- **Cloud Provider**: AWS
  - ECS Fargate (compute)
  - RDS PostgreSQL (databases)
  - DocumentDB (MongoDB-compatible)
  - ECR (container registry)
  - S3 (frontend hosting)
  - CloudFront (CDN)
  - Application Load Balancer
  - CloudWatch (logging/monitoring)

## Design Patterns

### Microservices Pattern
- Each service is independently deployable
- Services communicate via HTTP/REST
- Each service has its own database
- Services are loosely coupled

### API Gateway Pattern
- Single entry point for all client requests
- Request routing to appropriate services
- Cross-cutting concerns (logging, correlation IDs)
- Health check aggregation

### Database per Service Pattern
- Each microservice has its own database
- Data isolation and independence
- Service-specific data models
- No shared databases

### Authentication Pattern
- Centralized authentication in User Service
- JWT token-based authentication
- Token verification for protected endpoints
- Role-based access control

## Security Considerations

### Authentication & Authorization
- JWT tokens with expiration
- Password hashing with bcrypt (10 rounds)
- Role-based access control (Student, Staff, Admin)
- Token verification on protected endpoints

### Data Security
- Environment variables for sensitive data
- No hardcoded credentials
- Separate databases per service
- CORS configuration

### Network Security
- VPC isolation (AWS)
- Security groups
- Private subnets for databases
- HTTPS for frontend (CloudFront)

## Scalability Considerations

### Horizontal Scaling
- Stateless services (can run multiple instances)
- Load balancer distributes traffic
- ECS Fargate auto-scaling
- Database read replicas (future enhancement)

### Vertical Scaling
- Adjustable container resources (CPU/Memory)
- Database instance sizing
- RDS storage auto-scaling

### Caching (Future Enhancement)
- Redis for session management
- CloudFront edge caching
- Database query caching

## Monitoring & Observability

### Logging
- Structured logging with timestamps
- Request/response logging
- Correlation IDs for request tracing
- CloudWatch Logs (AWS)

### Health Checks
- Individual service health endpoints
- Aggregated health check in API Gateway
- Docker health checks
- ECS health checks

### Metrics (AWS)
- ECS service CPU/Memory usage
- RDS database metrics
- ALB request count and latency
- CloudWatch custom metrics

## Data Flow Examples

### Example 1: Student Creates a Ticket

1. Student logs in via frontend
2. Frontend sends credentials to API Gateway
3. API Gateway routes to User Service
4. User Service validates credentials, returns JWT
5. Student creates ticket with JWT token
6. API Gateway routes to Ticket Service
7. Ticket Service verifies token with User Service
8. Ticket Service creates ticket in PostgreSQL
9. Ticket Service calls Notification Service
10. Notification Service creates notification in MongoDB
11. Frontend receives success response
12. Frontend fetches updated notifications

### Example 2: Staff Updates Ticket Status

1. Staff member logs in (role: Staff)
2. Staff views all tickets (role-based access)
3. Staff updates ticket status to "In Progress"
4. Ticket Service verifies staff role
5. Ticket Service updates ticket in PostgreSQL
6. Notification sent to ticket creator
7. Student sees notification in real-time

### Example 3: Student Books a Room

1. Student views available rooms
2. Student selects room and time slot
3. Booking Service checks for conflicts
4. If no conflict, booking is created
5. Notification sent to student
6. Booking appears in student's booking list

## Deployment Architecture (AWS)

### Development Environment
- Docker Compose on local machine
- All services run locally
- Local PostgreSQL and MongoDB
- Hot reload for development

### Production Environment (AWS)
- ECS Fargate cluster with 5 services
- RDS PostgreSQL (3 instances)
- DocumentDB cluster
- Application Load Balancer
- S3 + CloudFront for frontend
- CloudWatch for monitoring

### CI/CD Pipeline
1. Developer pushes code to GitHub
2. GitHub Actions triggers
3. Tests run for all services
4. Docker images built
5. Images pushed to ECR
6. ECS services updated
7. Frontend deployed to S3
8. CloudFront cache invalidated

## Future Enhancements

### Technical
- [ ] Add Redis for caching
- [ ] Implement message queue (SQS/RabbitMQ)
- [ ] Add WebSocket for real-time notifications
- [ ] Implement API rate limiting
- [ ] Add comprehensive unit/integration tests
- [ ] Implement database migrations
- [ ] Add API versioning

### Features
- [ ] Email notifications
- [ ] SMS notifications
- [ ] File attachments for tickets
- [ ] Calendar integration for bookings
- [ ] Analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Admin panel for system management

### Operations
- [ ] Automated backups
- [ ] Disaster recovery plan
- [ ] Multi-region deployment
- [ ] Blue-green deployments
- [ ] Canary releases
- [ ] Performance monitoring
- [ ] Cost optimization

---

**Architecture Version**: 1.0  
**Last Updated**: December 2024
