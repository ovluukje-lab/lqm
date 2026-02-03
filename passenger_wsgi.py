# Voor webhosting met Passenger (Ruby/Python). Sommige hosts laden deze file automatisch.
import sys
import os

# Zorg dat de app-map in het pad zit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app as application
