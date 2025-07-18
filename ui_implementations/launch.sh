#!/bin/bash

echo "🤖 Multi-Model AI Assistant - Launch Script"
echo

echo "Checking if Flask backend is running..."
if ! curl -s http://localhost:5000/api/models > /dev/null 2>&1; then
    echo "❌ Flask backend not running! Please start unified_app.py first."
    echo
    echo "To start the Flask backend:"
    echo "  cd .."
    echo "  python unified_app.py"
    echo
    read -p "Press any key to exit..." -n1 -s
    exit 1
fi

echo "✅ Flask backend is running!"
echo

echo "Available UI Technologies:"
echo
echo "1. Flask + SocketIO (Current - Port 5000)"
echo "2. Streamlit (Port 8501)"
echo "3. React (Port 3000)"
echo "4. Gradio (Port 7860)"
echo "5. Technology Selector (HTML)"
echo

read -p "Choose a technology (1-5): " choice

case $choice in
    1)
        echo "Launching Flask app..."
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:5000
        elif command -v open > /dev/null; then
            open http://localhost:5000
        else
            echo "Please open http://localhost:5000 in your browser"
        fi
        ;;
    2)
        echo "Installing Streamlit requirements..."
        pip install -r requirements_streamlit.txt
        echo "Launching Streamlit app..."
        streamlit run streamlit_app.py
        ;;
    3)
        echo "Setting up React app..."
        cd react_app
        if [ ! -d "node_modules" ]; then
            echo "Installing React dependencies..."
            npm install
        fi
        echo "Launching React app..."
        npm start
        ;;
    4)
        echo "Installing Gradio requirements..."
        pip install -r requirements_gradio.txt
        echo "Launching Gradio app..."
        python gradio_app.py
        ;;
    5)
        echo "Opening Technology Selector..."
        if command -v xdg-open > /dev/null; then
            xdg-open index.html
        elif command -v open > /dev/null; then
            open index.html
        else
            echo "Please open index.html in your browser"
        fi
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo
echo "✅ Application launched successfully!"
