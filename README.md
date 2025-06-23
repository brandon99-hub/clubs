# School Club Management System

A Django-based web application for managing school clubs, events, and member communications.

## Features

- 🏫 Club Management
- 📅 Event Scheduling
- 💬 Real-time Messaging
- 👥 Member Management
- 🌙 Dark/Light Mode
- 📱 Responsive Design
- 🔐 User Authentication

## Tech Stack

- **Backend**: Django 4.2.7
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Database**: PostgreSQL (production), SQLite (development)
- **Real-time**: Django Channels + Redis
- **Task Queue**: Celery + Redis
- **Static Files**: WhiteNoise
- **Deployment**: Render

## Local Development

### Prerequisites

- Python 3.8+
- Redis (for channels and Celery)
- Virtual environment

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd DjangoProject2
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your local settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Redis** (for channels and Celery)
   ```bash
   # Install Redis or use Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Start Celery worker** (in a new terminal)
   ```bash
   celery -A DjangoProject24 worker --loglevel=info
   ```

## Deployment on Render

### Step 1: Prepare Your Repository

1. **Push your code to GitHub/GitLab**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Ensure these files are in your repository:**
   - `requirements.txt`
   - `build.sh`
   - `DjangoProject24/settings.py` (updated for production)

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with your GitHub/GitLab account
3. Connect your repository

### Step 3: Deploy Web Service

1. **Click "New +" → "Web Service"**
2. **Connect your repository**
3. **Configure the service:**

   **Basic Settings:**
   - **Name**: `your-app-name`
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn DjangoProject24.wsgi:application`

   **Environment Variables:**
   ```
   SECRET_KEY=your-super-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=your-app-name.onrender.com
   DATABASE_URL=postgres://... (provided by Render)
   REDIS_URL=redis://... (if using Redis service)
   ```

### Step 4: Add PostgreSQL Database

1. **Click "New +" → "PostgreSQL"**
2. **Configure:**
   - **Name**: `your-app-db`
   - **Database**: `your_app_db`
   - **User**: `your_app_user`
3. **Copy the DATABASE_URL** to your web service environment variables

### Step 5: Add Redis Service (Optional)

1. **Click "New +" → "Redis"**
2. **Configure:**
   - **Name**: `your-app-redis`
3. **Copy the REDIS_URL** to your web service environment variables

### Step 6: Configure Environment Variables

Add these to your web service:

```
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
DATABASE_URL=postgres://... (from PostgreSQL service)
REDIS_URL=redis://... (from Redis service, if using)
STATIC_URL=/static/
STATIC_ROOT=staticfiles/
MEDIA_URL=/media/
MEDIA_ROOT=media/
```

### Step 7: Deploy

1. **Click "Create Web Service"**
2. **Wait for build to complete**
3. **Your app will be available at**: `https://your-app-name.onrender.com`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Generated |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection | SQLite |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `STATIC_URL` | Static files URL | `/static/` |
| `STATIC_ROOT` | Static files directory | `staticfiles/` |
| `MEDIA_URL` | Media files URL | `/media/` |
| `MEDIA_ROOT` | Media files directory | `media/` |

## File Structure

```
DjangoProject2/
├── DjangoProject24/          # Django project settings
├── clubs/                    # Main app
│   ├── static/              # Static files
│   ├── templates/           # HTML templates
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   └── urls.py             # URL patterns
├── requirements.txt         # Python dependencies
├── build.sh                # Build script for Render
├── env.example             # Environment variables example
└── README.md               # This file
```

## Troubleshooting

### Common Issues

1. **Build fails on Render**
   - Check `requirements.txt` has all dependencies
   - Ensure `build.sh` is executable (`chmod +x build.sh`)

2. **Static files not loading**
   - Verify `STATIC_ROOT` is set correctly
   - Check WhiteNoise is configured properly

3. **Database connection errors**
   - Verify `DATABASE_URL` is correct
   - Check PostgreSQL service is running

4. **Redis connection errors**
   - Verify `REDIS_URL` is correct
   - Check Redis service is running

### Debug Mode

For debugging, temporarily set:
```
DEBUG=True
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Render documentation
3. Check Django deployment checklist

## License

This project is licensed under the MIT License. 