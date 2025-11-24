#!/usr/bin/env python3
"""
Trading Manager Flask Application

Main entry point for the trading manager web application.
This file imports from backend.app to maintain backward compatibility.
"""

from backend.app import create_app
import os

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting Trading Manager on http://localhost:{port}")
    print(f"Debug mode: {app.config.get('DEBUG', False)}")
    app.run(host='0.0.0.0', port=port)
