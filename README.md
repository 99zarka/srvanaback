# Srvana Backend API

A comprehensive Django-based backend API for the Srvana Service Platform, connecting customers (clients) with skilled service providers (technicians). The platform supports multiple service delivery models including direct hiring and competitive bidding systems.

## 🌟 Features

### Core Functionality
- **Multi-Role User Management**: Custom user system with Client, Technician, and Admin roles
- **Service Discovery & Management**: Categorized services with pricing and availability tracking
- **Dual Service Ordering Systems**:
  - **Direct Hire**: Clients can directly book specific technicians
  - **Bidding System**: Clients post projects and receive competitive offers
- **Real-time Communication**: Integrated chat system between clients and technicians
- **Financial Management**: Complete payment processing with escrow and commission handling
- **Dispute Resolution**: Built-in dispute management and resolution workflows
- **Notification System**: Real-time notifications for all platform activities
- **File Upload & Media Management**: Cloudinary integration for media storage
- **Comprehensive Reviews & Ratings**: Feedback system for service quality assessment

### Technical Features
- **RESTful API Design**: Clean, documented API endpoints following REST principles
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Google OAuth2 Integration**: Social authentication support
- **API Documentation**: Interactive Swagger UI and Redoc documentation
- **Database Optimization**: Efficient queries with proper indexing and relationships
- **Error Handling**: Comprehensive error handling and validation
- **Testing Suite**: Unit and integration tests for reliability

## 🏗️ Architecture

### Application Structure
```
srvanaback/
├── srvana/                 # Main project configuration
│   ├── settings.py        # Django settings with environment-specific configs
│   ├── urls.py           # Main URL routing configuration
│   └── test_settings.py  # Testing configuration
├── users/                 # User management and authentication
├── orders/               # Order processing and management
├── services/             # Service catalog and categories
├── chat/                 # Real-time messaging system
├── technicians/          # Technician-specific functionality
├── payments/             # Payment processing and transactions
├── notifications/        # Notification management
├── reviews/              # Review and rating system
├── disputes/             # Dispute resolution system
├── addresses/            # Location and address management
├── filesupload/          # File upload and media management
├── issue_reports/        # Issue tracking and reporting
├── transactions/         # Financial transaction records
└── api/                  # API utilities and shared components
```

### Database Models

#### Core Models
- **User**: Custom user model with role-based access, profile management, and technician-specific fields
- **UserType**: Enumeration for user roles (Client, Technician, Admin)
- **Service**: Service definitions with pricing, categories, and descriptions
- **ServiceCategory**: Hierarchical service categorization with Arabic name support
- **Order**: Central order management with status tracking and pricing
- **Payment**: Transaction records with payment method and status tracking

#### Supporting Models
- **Media**: File attachments and media management for orders
- **Complaint**: Customer complaints and resolution tracking
- **ProjectOffer**: Bidding system for service requests
- **ChatMessage**: Real-time communication records
- **Notification**: System and user notifications
- **Review**: Service and technician reviews with ratings

### API Endpoints Structure

```
/api/
├── users/                    # User management
│   ├── POST /register/       # User registration
│   ├── POST /login/          # Authentication
│   ├── GET /profile/         # User profile data
│   └── PUT /profile/         # Update profile
├── services/                 # Service catalog
│   ├── GET /                 # List all services
│   ├── GET /categories/      # Service categories
│   └── GET /{id}/            # Service details
├── orders/                   # Order management
│   ├── POST /create/         # Create new order
│   ├── GET /                 # List user orders
│   ├── GET /{id}/            # Order details
│   └── PUT /{id}/            # Update order
├── chat/                     # Messaging system
│   ├── GET /conversations/   # User conversations
│   ├── POST /message/        # Send message
│   └── GET /{id}/messages/   # Conversation messages
├── technicians/              # Technician functionality
│   ├── GET /browse/          # Browse available technicians
│   ├── GET /{id}/            # Technician profile
│   └── POST /verify/         # Technician verification
├── payments/                 # Payment processing
│   ├── POST /process/        # Process payment
│   ├── GET /transactions/    # Transaction history
│   └── POST /escrow/         # Escrow management
├── notifications/            # Notification system
│   ├── GET /                 # User notifications
│   ├── PUT /{id}/read/       # Mark as read
│   └── POST /send/           # Send notification
├── disputes/                 # Dispute management
│   ├── POST /create/         # Initiate dispute
│   ├── GET /                 # User disputes
│   └── PUT /{id}/resolve/    # Resolve dispute
└── reviews/                  # Review system
    ├── POST /                # Submit review
    ├── GET /technician/{id}/ # Technician reviews
    └── GET /service/{id}/    # Service reviews
```

## 🛠️ Technology Stack

### Core Technologies
- **Django 5.2.1**: Modern Python web framework
- **Django Rest Framework (DRF)**: Powerful API framework
- **PostgreSQL**: Robust relational database (configured for Aiven Cloud)
- **Python 3.10+**: Latest Python features and performance

### Authentication & Security
- **SimpleJWT**: JWT token authentication with refresh tokens
- **Google OAuth2**: Social authentication integration
- **Custom Permissions**: Role-based access control system
- **CORS Support**: Cross-origin resource sharing configuration

### External Services
- **Cloudinary**: Cloud-based media storage and management
- **Aiven Cloud**: Managed PostgreSQL database hosting

### Development & Documentation
- **drf-yasg**: Swagger/OpenAPI 3 documentation generation
- **Django Admin**: Built-in administration interface
- **Django Tests**: Comprehensive testing framework
- **Docker Support**: Containerized deployment ready

## 📋 Prerequisites

- **Python 3.10 or higher**
- **PostgreSQL 12+** (or use configured Aiven Cloud instance)
- **pip** (Python package installer)
- **Virtual environment tool** (venv or virtualenv)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd srvanaback
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root (optional - uses settings.py defaults):

```env
# Database Configuration
DATABASE_URL=your_postgresql_connection_string

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# JWT Configuration
SECRET_KEY=your_django_secret_key

# OAuth Configuration
GOOGLE_OAUTH2_KEY=your_google_client_id
GOOGLE_OAUTH2_SECRET=your_google_client_secret

# Production Settings
DJANGO_PRODUCTION=False
DEBUG=True
```

### 5. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Load sample data (if available)
python populate_data.py
```

### 6. Run Development Server
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## 🔧 Configuration

### Settings Structure
- **Development**: Uses SQLite by default, debug enabled
- **Production**: PostgreSQL via Aiven Cloud, debug disabled
- **Testing**: Isolated test database with fast test runner

### Key Configuration Files
- `srvana/settings.py`: Main configuration with environment detection
- `srvana/test_settings.py`: Testing-specific configuration
- `requirements.txt`: Python dependencies

### Environment Variables
Key environment variables for customization:
- `DJANGO_PRODUCTION`: Toggle production settings
- `CLOUDINARY_*`: Media storage configuration
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Django secret key for security

## 📚 API Documentation

Once the server is running, comprehensive API documentation is available at:

### Interactive Documentation
- **Swagger UI**: `http://127.0.0.1:8000/swagger/`
  - Interactive API testing interface
  - Request/response examples
  - Authentication testing

- **Redoc**: `http://127.0.0.1:8000/redoc/`
  - Clean, readable API documentation
  - Request/response schemas
  - Authentication requirements

### API Testing
```bash
# Run the provided test script
test_api.bat

# Or run Django tests
python manage.py test

# Run specific app tests
python manage.py test orders
```

## 🧪 Testing

### Test Structure
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Service Flow Tests**: End-to-end workflow testing
- **Authentication Tests**: Security and permission testing

### Running Tests
```bash
# All tests
python manage.py test

# Specific app tests
python manage.py test orders.tests_service_flows

# With coverage
python manage.py test --verbosity=2

# Using test settings
python manage.py test --settings=srvana.test_settings
```

## 🐳 Docker Deployment

The application includes Docker support for containerized deployment:

```bash
# Build Docker image
docker build -t srvana-backend .

# Run container
docker run -p 8000:8000 srvana-backend
```

### Docker Configuration
- `Dockerfile`: Multi-stage build for optimization
- `docker-compose.yml`: Complete stack deployment (if provided)
- Environment variables for container configuration

## 🔒 Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access**: Client, Technician, Admin permissions
- **OAuth2 Integration**: Social login support
- **CSRF Protection**: Cross-site request forgery prevention

### Data Protection
- **Input Validation**: Comprehensive request validation
- **SQL Injection Prevention**: ORM-based query protection
- **XSS Protection**: Template and API response sanitization
- **Secure Headers**: Security-focused HTTP headers

## 📊 Monitoring & Logging

### Built-in Features
- **Django Admin**: Administrative interface for monitoring
- **Database Logging**: Query performance monitoring
- **Error Tracking**: Comprehensive error logging
- **API Request Logging**: Request/response tracking

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request
5. Code review and merge

### Code Standards
- **PEP 8**: Python code style guidelines
- **DRF Best Practices**: API design principles
- **Test Coverage**: Maintain high test coverage
- **Documentation**: Update docs for new features

## 📝 License

This project is licensed under the BSD License - see the LICENSE file for details.

## 🆘 Support & Documentation

### Additional Resources
- **Django Documentation**: https://docs.djangoproject.com/
- **DRF Documentation**: https://www.django-rest-framework.org/
- **API Testing**: Use provided Swagger interface
- **Admin Interface**: `/admin/` for system administration

### Troubleshooting
- **Database Issues**: Check PostgreSQL connection and migrations
- **Authentication Errors**: Verify JWT configuration and OAuth settings
- **File Upload Issues**: Confirm Cloudinary configuration
- **Performance**: Monitor database queries and API response times

---

**Built with ❤️ using Django and Django Rest Framework**
