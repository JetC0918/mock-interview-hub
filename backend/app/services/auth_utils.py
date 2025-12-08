from datetime import datetime, timedelta
from typing import Optional

# Very basic mock auth
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    # In real app, jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return "mock_token_" + data["sub"] 
