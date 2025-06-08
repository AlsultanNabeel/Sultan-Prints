#!/bin/bash
# Script to check the project configuration

echo "🔍 Checking project configuration..."

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment: Found"
else
    echo "❌ Virtual environment: Not found"
    echo "   Run './setup.sh' to create it"
fi

# Check .env file
if [ -f ".env" ]; then
    echo "✅ .env file: Found"
else
    echo "❌ .env file: Not found"
    echo "   Run './setup.sh' to create it"
fi

# Check critical directories
if [ -d "static/uploads/custom" ] && [ -d "static/uploads/designs" ]; then
    echo "✅ Upload directories: Found"
else
    echo "❌ Upload directories: Missing"
    echo "   Run 'mkdir -p static/uploads/custom static/uploads/designs' to create them"
fi

if [ -d "logs" ]; then
    echo "✅ Logs directory: Found"
else
    echo "❌ Logs directory: Not found"
    echo "   Run 'mkdir -p logs' to create it"
fi

# Check Python 3 installation
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python 3: Found ($PYTHON_VERSION)"
else
    echo "❌ Python 3: Not found"
    echo "   Install Python 3 to continue"
fi

# Check MySQL database
if command -v mysql >/dev/null 2>&1; then
    if mysql -u root -e "USE tshirt_store" 2>/dev/null; then
        echo "✅ Database: Found"
    else
        echo "❌ Database: Not found or not accessible"
        echo "   Create the database with: 'mysql -u root -e \"CREATE DATABASE tshirt_store CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\"'"
    fi
else
    echo "⚠️ MySQL client is not installed, can't check the database"
fi

# Count files in each category
NUM_PYTHON_FILES=$(find . -name "*.py" | wc -l)
NUM_TEMPLATE_FILES=$(find ./templates -name "*.html" | wc -l)
NUM_STATIC_FILES=$(find ./static -type f | wc -l)

echo "📊 Project statistics:"
echo "   - Python files: $NUM_PYTHON_FILES"
echo "   - HTML templates: $NUM_TEMPLATE_FILES"
echo "   - Static files: $NUM_STATIC_FILES"

# Check if the virtual environment is active
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "\n📋 Installed dependencies:"
    pip freeze | grep -E "Flask|SQLAlchemy|PyMySQL|Pillow|WTForms"
else
    echo -e "\n⚠️ Virtual environment is not active. Activate it with:"
    echo "   source venv/bin/activate"
fi

echo -e "\n💡 To start:"
echo "   1. Run 'sh setup.sh' to set up the environment (if not already done)"
echo "   2. Run 'sh start.sh' to start the application"
echo "   3. Access http://localhost:5002 in your browser"
