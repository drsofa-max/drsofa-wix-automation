# Dr. Sofa Wix SEO Blog Automation Engine

Complete full-stack system for automating SEO-optimized blog post generation and publishing to Wix sites using OpenAI GPT-4 and Cloudflare Workers.

## Features

✅ **Blog Generation** - AI-powered SEO blog posts via OpenAI GPT-4
✅ **Wix Publishing** - Direct publishing to Wix blog pages
✅ **Automation** - Schedule weekly blog posts automatically
✅ **Multi-Site** - Manage multiple Wix sites from one dashboard
✅ **REST API** - Complete REST API for programmatic access
✅ **User Auth** - JWT-based authentication and multi-user support
✅ **Analytics** - Dashboard with posts, sites, and schedule stats

## Tech Stack

**Backend:**
- Python 3.9+
- Flask (web framework)
- SQLAlchemy (ORM)
- PostgreSQL (database)
- OpenAI API (blog generation)
- JWT (authentication)

**Frontend:**
- React 18
- Tailwind CSS
- Axios
- React Query

**Deployment:**
- Railway or Heroku (backend)
- Vercel (frontend)
- Cloudflare Workers (Wix API proxy)

## Prerequisites

1. **OpenAI Account** - Get API key from https://platform.openai.com
2. **Wix Account** - With blog pages and API credentials
3. **Cloudflare Worker** - Deploy the proxy worker (see setup guide)
4. **GitHub Account** - For version control and deployment
5. **Railway Account** - For hosting (https://railway.app)

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/drsofa-max/drsofa-wix-automation.git
cd drsofa-wix-automation
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env with your keys:
# - OPENAI_API_KEY
# - DATABASE_URL
# - JWT_SECRET_KEY
# - WIX API details
```

### 5. Initialize Database

```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

### 6. Run Development Server

```bash
python app.py
```

Server runs on `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Credentials
- `POST /api/credentials/save` - Save Wix API credentials
- `GET /api/credentials/get` - Get saved credentials
- `POST /api/credentials/test` - Test API connection
- `GET /api/credentials/sites` - Get configured sites

### Posts
- `POST /api/posts/generate` - Generate new blog post
- `GET /api/posts` - List all posts
- `GET /api/posts/<id>` - Get single post
- `POST /api/posts/<id>/publish` - Publish to Wix
- `DELETE /api/posts/<id>` - Delete post

### Schedule
- `GET /api/schedule` - Get all schedules
- `POST /api/schedule` - Create schedule
- `PUT /api/schedule/<id>` - Update schedule
- `POST /api/schedule/<id>/toggle` - Enable/disable
- `DELETE /api/schedule/<id>` - Delete schedule

### Stats
- `GET /api/stats/dashboard` - Dashboard stats
- `GET /api/stats/posts-by-month` - Posts per month
- `GET /api/stats/posts-by-status` - Distribution by status
- `GET /api/stats/posts-by-site` - Distribution by site
- `GET /api/stats/topics` - Distribution by topic

## Deployment to Railway

### 1. Connect GitHub

```bash
# Push to GitHub
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Authorize and select `drsofa-wix-automation`
5. Railway auto-detects Python

### 3. Configure Environment

In Railway dashboard:

1. Click "Variables"
2. Add from `.env.example`:
   - `OPENAI_API_KEY` - Your OpenAI key
   - `DATABASE_URL` - Railway PostgreSQL (auto-created)
   - `JWT_SECRET_KEY` - Generate: `python -c 'import secrets; print(secrets.token_hex(32))'`
   - `FLASK_ENV` - `production`
   - And others from `.env.example`

3. Click "Deploy"

### 4. Database Migrations

```bash
# In Railway terminal
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
```

Your backend is live! Note the Railway URL.

## Frontend Deployment (React)

Coming soon - React dashboard code.

For now, use the HTML dashboard at `/frontend/public/index.html`

## Usage

### 1. Register Account

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

### 2. Save Credentials

```bash
curl -X POST http://localhost:5000/api/credentials/save \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "wix_api_key":"IST.eyJ...",
    "wix_account_id":"9dbaf23a-...",
    "cloudflare_proxy_url":"https://worker.workers.dev",
    "sites":[{
      "site_name":"SofaDisassembly.com",
      "domain":"sofadisassembly.com",
      "wix_site_id":"7cf325e6-...",
      "city":"New York",
      "state":"NY"
    }]
  }'
```

### 3. Generate Post

```bash
curl -X POST http://localhost:5000/api/posts/generate \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id":1,
    "topic":"disassembly",
    "tone":"helpful",
    "length":"medium"
  }'
```

### 4. Publish to Wix

```bash
curl -X POST http://localhost:5000/api/posts/1/publish \
  -H "Authorization: Bearer <TOKEN>"
```

### 5. Setup Automation

```bash
curl -X POST http://localhost:5000/api/schedule \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id":1,
    "frequency":"weekly",
    "day_of_week":0,
    "hour_of_day":9,
    "enabled":true,
    "topic":"disassembly",
    "tone":"helpful",
    "length":"medium"
  }'
```

## Architecture

```
Frontend (React)
    ↓
Backend API (Flask)
    ↓
Database (PostgreSQL)
    ↓
OpenAI GPT-4 (blog generation)
Cloudflare Worker (Wix API proxy)
```

## Security

- API keys encrypted at rest
- JWT authentication
- Environment variables for secrets
- CORS enabled only for trusted origins
- Rate limiting on API endpoints

## Cost Estimates

**Monthly:**
- Railway: $5-15 (web dyno + PostgreSQL)
- OpenAI API: $10-30 (depending on usage)
- Cloudflare: Free (worker included)
- **Total: $15-45/month**

## Troubleshooting

**401 Unauthorized from Wix**
- Check API key is correct
- Verify blog page exists at /blog on Wix site
- Test connection with `/api/credentials/test`

**OpenAI rate limit**
- Wait a few minutes before retrying
- Consider upgrading OpenAI account

**Database errors**
- Check DATABASE_URL is correct
- Run migrations: `db.create_all()`

## Support

For issues:
1. Check logs in Railway dashboard
2. Review API responses
3. Open GitHub issue with error details

## License

MIT - See LICENSE file

## Next Steps

1. Deploy to Railway
2. Configure Wix credentials
3. Test blog generation
4. Enable automation
5. Monitor dashboard

Happy automating! 🚀
