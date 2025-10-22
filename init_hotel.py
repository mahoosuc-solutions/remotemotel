#!/usr/bin/env python3
"""
Initialize Hotel Management System

This script initializes the hotel management system with sample data.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from packages.hotel.init_data import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
