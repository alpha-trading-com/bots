from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from typing import Optional

from bcrypt import hashpw, gensalt, checkpw

security = HTTPBasic()

# In a real application, you would store these in a database
# and use proper password hashing
USERS = {
    "admin": "$2b$12$4a8XSpvI8cvB6puudnr2TeFfnohvwRH3jVfJ/9ITcQl5nCdy0.Cp2"
}

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    stored_hash = USERS[credentials.username]
    if not checkpw(credentials.password.encode(), stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username