#!/bin/bash

# Create admin user if it doesn't exist
if [ -n "$ADMIN_PASSWORD" ]; then
    python3 - <<EOF
import bcrypt
import os
from sqlalchemy import create_engine
from jupyterhub.orm import User, Base

# Create database tables if they don't exist
engine = create_engine('sqlite:///jupyterhub.sqlite')
Base.metadata.create_all(engine)

# Create session
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

# Check if admin user exists
admin_user = session.query(User).filter(User.name == 'admin').first()
if not admin_user:
    # Create admin user
    admin_user = User(name='admin', admin=True)
    session.add(admin_user)
    
    # Create password hash for NativeAuthenticator
    from nativeauthenticator.orm import UserInfo
    encoded_pw = bcrypt.hashpw(os.environ['ADMIN_PASSWORD'].encode(), bcrypt.gensalt())
    user_info = UserInfo(username='admin', password=encoded_pw)
    session.add(user_info)
    
    session.commit()
    print("Admin user created successfully")
else:
    print("Admin user already exists")
EOF
fi

# Start JupyterHub
exec jupyterhub -f /srv/jupyterhub/jupyterhub_config.py
