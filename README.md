# ShopSphere: Distributed Commerce Platform
> **A DevOps-Driven E-Commerce Application**  
> College DevOps Project Submission

---

## 📌 Project Overview
**ShopSphere** is a lightweight, responsive, and production-ready e-commerce platform built to demonstrate an end-to-end DevOps lifecycle — from development, automated testing, continuous integration, containerization, to orchestration.

Designed with a **modular monolithic architecture** (avoiding unnecessary microservices complexity while maintaining clean separation of concerns), ShopSphere provides an Amazon/Flipkart-style user experience backed by robust DevOps infrastructure.

---

## 🛠️ Technology Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | HTML5, Vanilla CSS3, JavaScript | Modern, glassmorphic, responsive store UI with search, cart badges, and instant filters. |
| **Backend** | Python 3 (Flask) | Modular Flask application with application factory and Blueprints (`catalog`, `cart`, `checkout`, `main`). |
| **Database** | SQLite3 | Parameterized SQL queries, auto-initializing schema, and seeded product catalog. |
| **Testing** | Pytest | 19 automated unit and integration tests covering catalog, cart, checkout, and database integrity. |
| **Version Control** | Git & GitHub | Modular branching and commit tracking. |
| **CI/CD** | Jenkins | Declarative pipeline (`Jenkinsfile`) automating build, test, and container packaging. |
| **Containerization**| Docker | Multi-stage Docker container with native health probes. |
| **Orchestration** | Kubernetes & Minikube | High-availability deployment (`2 replicas`), NodePort service, and ConfigMap. |

---

## 🏛️ Application & DevOps Architecture

```
                                  +-----------------------+
                                  |   Developer / Git     |
                                  +-----------+-----------+
                                              | git push
                                              v
+------------------+              +-----------------------+
|  User Browser    |              |   GitHub Repository   |
+--------+---------+              +-----------+-----------+
         |                                    | Webhook / Polling
         | HTTP (Port 5000 / NodePort 30080)   v
         |                        +-----------------------+
         |                        |   Jenkins CI Pipeline |
         |                        |  - Checkout           |
         |                        |  - Pytest Test Suite  |
         |                        |  - Docker Build       |
         |                        |  - Deploy to K8s      |
         |                        +-----------+-----------+
         |                                    |
         v                                    v
+---------------------------------------------------------+
|                  Minikube Kubernetes Cluster            |
|                                                         |
|  +---------------------------------------------------+  |
|  |           shopsphere-service (NodePort 30080)     |  |
|  +-------------------------+-------------------------+  |
|                            |                            |
|             +--------------+--------------+             |
|             v                             v             |
|  +--------------------+        +--------------------+   |
|  | Pod 1: ShopSphere  |        | Pod 2: ShopSphere  |   |
|  | - Flask App        |        | - Flask App        |   |
|  | - SQLite DB        |        | - SQLite DB        |   |
|  | - Health Probe     |        | - Health Probe     |   |
|  +--------------------+        +--------------------+   |
+---------------------------------------------------------+
```

---

## 📂 Repository Directory Layout

```text
shopsphere/
├── app/
│   ├── __init__.py          # Flask Application Factory & Global Context Processors
│   ├── config.py            # Environment Configuration (Dev & Testing)
│   ├── db.py                # Safe SQLite Connection Manager & Auto-Seeder
│   ├── schema.sql           # Database DDL Schema (categories, products, orders, items)
│   ├── seed_data.py         # Sample Product Catalog Data
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── catalog.py       # Homepage, category filtering, search, and product details
│   │   ├── cart.py          # Session-backed cart: add, update, remove, clear, arithmetic
│   │   ├── checkout.py      # Demo checkout form validation, SQLite persistence, receipt
│   │   └── main.py          # Health check endpoint (/api/health)
│   ├── static/
│   │   └── css/style.css    # Responsive CSS Design System (Outfit + Inter typography)
│   └── templates/
│       ├── base.html        # Shared base template with search bar and dynamic cart counter
│       ├── index.html       # Storefront with category chips and product grid
│       ├── product.html     # Product detail view with quantity stepper
│       ├── cart.html        # Cart view with item list and shipping calculator
│       ├── checkout.html    # Demo checkout customer form with validation
│       └── order_confirmation.html # Receipt and SQLite record confirmation
├── tests/
│   ├── conftest.py          # Pytest fixtures and isolated temporary database
│   ├── test_init.py         # Database schema & health check tests
│   ├── test_catalog.py      # Catalog, search, and category filter tests
│   ├── test_cart.py         # Cart arithmetic, shipping, and update tests
│   └── test_checkout.py     # Checkout validation & SQLite order persistence tests
├── k8s/
│   ├── configmap.yaml       # Kubernetes ConfigMap for environment variables
│   ├── deployment.yaml      # Kubernetes Deployment (2 replicas + health probes)
│   └── service.yaml         # Kubernetes NodePort Service (Port 30080)
├── Dockerfile               # Container build definition with HEALTHCHECK
├── .dockerignore            # Docker ignore patterns
├── Jenkinsfile              # Declarative CI/CD pipeline script
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation & execution guide
```

---

## 🚀 Execution Guide

### 1. Local Development Setup

#### Clone & Enter the Directory:
```bash
git clone https://github.com/atharvkothawale/shopsphere.git
cd shopsphere
```

#### Install Dependencies:
```bash
python -m pip install -r requirements.txt
```

#### Start the Application:
```bash
python run.py
```
Open your browser at: **`http://localhost:5000`**
* The database `instance/shopsphere.db` is automatically created and seeded with 13 sample products on first launch!

---

### 2. Running Automated Tests

Execute the full automated Pytest test suite:
```bash
python -m pytest -v
```

Expected Output:
```text
tests/test_cart.py::test_cart_empty_state PASSED
tests/test_cart.py::test_add_to_cart_and_summary PASSED
tests/test_cart.py::test_cart_shipping_calculation_under_threshold PASSED
tests/test_cart.py::test_cart_update_quantity PASSED
tests/test_cart.py::test_cart_remove_item PASSED
tests/test_cart.py::test_cart_clear PASSED
tests/test_catalog.py::test_homepage_catalog_listing PASSED
tests/test_catalog.py::test_category_filter PASSED
tests/test_catalog.py::test_product_search_success PASSED
tests/test_catalog.py::test_product_search_empty PASSED
tests/test_catalog.py::test_product_detail_page PASSED
tests/test_catalog.py::test_product_detail_404 PASSED
tests/test_checkout.py::test_checkout_redirect_when_cart_empty PASSED
tests/test_checkout.py::test_checkout_form_validation_errors PASSED
tests/test_checkout.py::test_order_placement_and_database_persistence PASSED
tests/test_checkout.py::test_order_confirmation_404 PASSED
tests/test_init.py::test_database_schema_and_seed PASSED
tests/test_init.py::test_health_check_endpoint PASSED
tests/test_init.py::test_homepage_rendering PASSED

============================= 19 passed in 1.00s =============================
```

---

### 3. Docker Containerization

#### Build the Docker Image:
```bash
docker build -t shopsphere:latest .
```

#### Run the Container:
```bash
docker run -d -p 5000:5000 --name shopsphere-app shopsphere:latest
```

#### Verify Container Health:
```bash
docker ps
curl http://localhost:5000/api/health
```

---

### 4. Kubernetes Deployment on Minikube

### Kubernetes Configuration Details

The Kubernetes manifests are located in the `k8s/` directory.

**Deployment (`deployment.yaml`)**
- Deployment name: `shopsphere-deployment`
- Replicas: 2
- Container image: `shopsphere:1.0`
- Container port: `5000`
- Image pull policy: `IfNotPresent`
- Resource requests per pod: 128 MiB memory and 100m CPU.
- Resource limits per pod: 256 MiB memory and 250m CPU.
- Readiness and liveness probes check `/api/health` on port 5000.
- Environment variables are loaded from `shopsphere-config`.

**Service (`service.yaml`)**
- Service name: `shopsphere-service`
- Type: `NodePort`
- Service port: `5000`
- Target port: `5000`
- NodePort: `30080`
- Selects application pods using the label `app: shopsphere`.

**ConfigMap (`configmap.yaml`)**

The `shopsphere-config` ConfigMap defines these environment variables:

| Variable | Value |
|---|---|
| `PORT` | `5000` |
| `FLASK_ENV` | `production` |
| `DATABASE_PATH` | `/app/instance/shopsphere.db` |

---

### 5. Jenkins CI/CD Pipeline
## Jenkins Continuous Integration

The project includes a `Jenkinsfile` that defines a Jenkins pipeline
for automating the ShopSphere build, testing, and deployment process.

### Pipeline Stages

1. **Checkout SCM:** Retrieves the source code from the configured Git repository.
2. **Environment & Dependencies:** Verifies the Python environment and installs the dependencies listed in `requirements.txt`.
3. **Automated Testing (Pytest):** Executes the automated test suite using Pytest and generates a JUnit test report.
4. **Docker Build & Image Packaging:** Builds Docker images tagged with the build number and `latest`.
5. **Deploy to Kubernetes (Minikube):** Applies the Kubernetes ConfigMap, Deployment, and Service manifests, then checks the deployment rollout status.

### Pipeline Post Actions

- **Success:** Displays a message indicating that the pipeline completed successfully.
- **Failure:** Displays a message indicating that the pipeline encountered an error.
- **Always:** Attempts to clean the Jenkins workspace after the pipeline finishes.

The pipeline is defined in the root-level `Jenkinsfile`.
Its execution depends on the availability and configuration of the
required tools, dependencies, Jenkins plugins, Docker, and Kubernetes.

---

## 🎯 Key Application Features Walkthrough

1. **Brand Homepage**: Sleek dark/light contrast hero banner with live status indicators.
2. **Category Filtering**: Instant category navigation (`Electronics`, `Fashion`, `Home & Kitchen`, `Books & Tech`).
3. **Keyword Search**: Instant search matching product titles and descriptions.
4. **Product Details**: Full product description, stock level, image preview, and quantity stepper.
5. **Shopping Cart**:
   - Add/Remove products.
   - Dynamic quantity adjustment.
   - Real-time subtotal, 5% estimated tax, and free shipping on orders above ₹999.
6. **Demo Checkout**:
   - Customer information form (Name, Email, Phone, Delivery Address).
   - Server-side validation with user feedback.
   - Simulated payment selection (Demo Cash on Delivery / Demo Card).
7. **SQLite Persistence**:
   - Saves orders in `orders` table.
   - Saves item snapshots in `order_items` table.
8. **Order Receipt Confirmation**:
   - Displays unique reference (`#SS-YYYYMMDD-XXXXXX`), customer details, itemized table, and total.

---

## 🎓 College Viva & Review Q&A

<details>
<summary><strong>Q1: Why did you choose a Modular Monolith instead of Microservices?</strong></summary>
<em>A: For an academic and mid-sized e-commerce workload, microservices introduce unnecessary operational overhead (service discovery, distributed transactions, network latency). A modular monolith with Flask Blueprints enforces clean separation of concerns while keeping deployment, testing, and containerization simple, efficient, and reliable.</em>
</details>

<details>
<summary><strong>Q2: How is database persistence managed in the Docker container and Kubernetes?</strong></summary>
<em>A: ShopSphere configures SQLite in an isolated <code>instance/</code> directory. In Kubernetes, the app automatically initializes and seeds the database on startup if it doesn't exist, and can be mounted to a PersistentVolumeClaim (PVC) for production storage.</em>
</details>

<details>
<summary><strong>Q3: How are health checks implemented for Kubernetes?</strong></summary>
<em>A: The app exposes <code>/api/health</code>, which performs a real-time query check on the SQLite database and returns HTTP 200 with JSON stats. The Kubernetes Deployment uses this endpoint for both <code>readinessProbe</code> and <code>livenessProbe</code>.</em>
</details>

---

## 👥 Student Contributions
- Team members can test features independently and commit their assigned modules using standard Git workflow:
```bash
git add .
git commit -m "feat: implement <module_name>"
git push origin main
```
## Git Collaboration Workflow

The team uses Git and GitHub to manage project changes.

1. Clone the repository.
2. Create an individual feature branch.
3. Make the assigned change.
4. Commit the changes.
5. Push the branch to GitHub.
6. Create a Pull Request targeting main.
7. Review and merge the Pull Request.

## Database Initialization

ShopSphere uses SQLite for database storage and Python's built-in `sqlite3` module to manage database connections. The database path is configured through the Flask application's configuration.

### Database Connection

The `app/db.py` file manages database connections using the `get_db()` function. It stores the connection in Flask's `g` object, enables row-based access with `sqlite3.Row`, and enforces foreign key constraints.

    docker run -p 5000:5000 shopsphere:1.0

## Application Health Check

The application exposes a health-check endpoint to verify server status and database connectivity.

- **Endpoint:** `/api/health`
- **Method:** `GET`
- **Port / Local URL:** `http://127.0.0.1:5000/api/health`

### Behavior & Database Verification

When requested, the endpoint connects to the SQLite database and runs real-time queries to count loaded categories and products before returning an HTTP `200` response.

### Example Response (`200 OK`)

```json
{
  "status": "healthy",
  "service": "ShopSphere",
  "version": "1.0.0",
  "database": "connected",
  "categories_loaded": 5,
  "products_loaded": 20
}
