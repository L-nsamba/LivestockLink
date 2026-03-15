# This file ensures the Python can import project modules from the root folder when running pytests from anywhere
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))