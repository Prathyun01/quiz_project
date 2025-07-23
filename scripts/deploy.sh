#!/bin/bash
set -e

echo "🚀 Starting StudyHub deployment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "👤 Setting up admin user..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@studyhub.com', 'admin123')
    print("Admin user created: admin/admin123")
else:
    print("Admin user already exists")
END

# Create sample data
echo "📊 Creating sample data..."
python manage.py create_sample_data

echo "✅ Deployment completed successfully!"
echo ""
echo "🎓 StudyHub is ready to use!"
echo "🌐 Access the application at: http://localhost:8000"
echo "🔧 Admin panel at: http://localhost:8000/admin"
echo "👤 Admin credentials: admin / admin123"
echo ""
echo "🚀 To start the development server:"
echo "   python manage.py runserver"
echo ""
echo "📧 Don't forget to configure your email settings in .env file"
echo "🤖 Add your AI API keys for quiz generation features"
