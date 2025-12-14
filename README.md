# LinkedIn Insights Microservice

A microservice to scrape and analyze LinkedIn company pages, providing insights on pages, posts, comments, and employees.

## Features

- Scrape LinkedIn company pages by Page ID
- Store page details, posts, comments, and employee information
- RESTful API with filtering and pagination
- Real-time scraping when data is not in database

## Setup

### Quick Start with Supabase (Free Cloud Database - Recommended)

Supabase provides a free PostgreSQL database in the cloud - no local installation needed!

1. **Create a Supabase account and project:**
   - Go to [https://supabase.com](https://supabase.com)
   - Sign up for a free account
   - Create a new project (takes ~2 minutes)
   - Wait for the database to be ready

2. **Get your database connection string:**
   - In your Supabase project dashboard, go to **Settings** → **Database**
   - Find the **Connection string** section
   - Copy the **URI** connection string (it looks like: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`)
   - Replace `[YOUR-PASSWORD]` with your actual database password (found in the same settings page)

3. **Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Set up environment variables:**
```bash
cp .env.example .env
```

5. **Update `.env` with your Supabase connection string:**
```
DATABASE_URL=postgresql://postgres:your-password@db.your-project-ref.supabase.co:5432/postgres
```

6. **Initialize database:**
```bash
python -c "from database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"
```

7. **Start the server:**
```bash
python run.py
```
or
```bash
uvicorn main:app --reload
```

That's it! The API will be available at `http://localhost:8000`

### Alternative: Quick Start with SQLite (Local File Database)

The application can also use SQLite by default (no database server needed):

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

2. Initialize database (creates `linkedin_insights.db` file):
```bash
python -c "from database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"
```

3. Start the server:
```bash
python run.py
```
or
```bash
uvicorn main:app --reload
```

### Using Local PostgreSQL (Optional)

If you prefer running PostgreSQL locally, you have two options:

#### Option A: Docker Compose

1. Start PostgreSQL database:
```bash
docker-compose up -d
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Update `.env` with PostgreSQL URL:
```
DATABASE_URL=postgresql://user:password@localhost:5432/linkedin_insights
```

5. Initialize database:
```bash
python -c "from database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"
```

6. Start the server:
```bash
python run.py
```

#### Option B: Manual PostgreSQL Setup

1. Install PostgreSQL and create database:
```sql
CREATE DATABASE linkedin_insights;
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Configure database in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/linkedin_insights
```

5. Initialize database:
```bash
python -c "from database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"
```

6. Start the server:
```bash
uvicorn main:app --reload
```

## API Endpoints

### Get Page by ID
```
GET /api/pages/{page_id}
```
Returns page details. If page is not in database, scrapes in real-time.

### Search Pages
```
GET /api/pages?min_followers=20000&max_followers=40000&name_search=tech&industry=Technology&page=1&page_size=10
```
Search pages with filters:
- `min_followers`: Minimum follower count
- `max_followers`: Maximum follower count
- `name_search`: Search by page name (partial match)
- `industry`: Filter by industry
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 100)

### Get Page Followers
```
GET /api/pages/{page_id}/followers?page=1&page_size=10
```
Get list of followers for a page (Note: Requires LinkedIn API for full functionality)

### Get Recent Posts
```
GET /api/pages/{page_id}/posts?limit=15
```
Get recent posts of a page (limit: 1-25)

### Get Page Employees
```
GET /api/pages/{page_id}/employees?page=1&page_size=10
```
Get list of employees working at the page

### Scrape Page
```
POST /api/pages/{page_id}/scrape
```
Manually trigger scraping for a page ID

### Health Check
```
GET /health
```
Check service health status

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Configuration

The application uses environment variables for configuration. A `.env` file is provided with default values.

### Environment Variables

- `DATABASE_URL`: Database connection string (default: `sqlite:///./linkedin_insights.db`)
- `SECRET_KEY`: Secret key for application security
- `DEBUG`: Enable debug mode (default: `True`)
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)
- `LINKEDIN_BASE_URL`: LinkedIn base URL (default: `https://www.linkedin.com`)
- `SCRAPER_TIMEOUT`: Scraper timeout in milliseconds (default: `60000`)
- `SCRAPER_HEADLESS`: Run browser in headless mode (default: `True`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

Copy `.env.example` to `.env` and modify as needed:
```bash
cp .env.example .env
```

## Testing

### Running Tests

The project includes comprehensive tests. Run them using:

```bash
# Simple test script (recommended)
python test_app.py

# Or using pytest (if available)
pytest tests/ -v
```

The test suite includes:
- Configuration loading tests
- API endpoint tests
- Database integration tests
- Pagination and filtering tests

## Postman Collection

Import `LinkedIn_Insights.postman_collection.json` into Postman for API testing.

The collection includes:
- All API endpoints with example requests
- Environment variables for `base_url` and `page_id`
- Pre-configured query parameters for filtering

## Example Usage

1. Scrape a LinkedIn page:
```bash
curl -X POST http://localhost:8000/api/pages/deepsolv/scrape
```

2. Get page details:
```bash
curl http://localhost:8000/api/pages/deepsolv
```

3. Search pages by follower range:
```bash
curl "http://localhost:8000/api/pages?min_followers=20000&max_followers=40000"
```

4. Get recent posts:
```bash
curl http://localhost:8000/api/pages/deepsolv/posts?limit=15
```

