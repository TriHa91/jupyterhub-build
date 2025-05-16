import os, nativeauthenticator
import sys
from dockerspawner import DockerSpawner

c = get_config()

# JupyterHub configuration
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 7443  # Use HTTPS port
c.JupyterHub.hub_ip = '0.0.0.0'
#c.JupyterHub.hub_port = 6043
# SSL Configuration
c.JupyterHub.ssl_key = '/srv/jupyterhub/ssl/jupyterhub.key'
c.JupyterHub.ssl_cert = '/srv/jupyterhub/ssl/jupyterhub.crt'
c.JupyterHub.db_url = "postgresql://postgres:postgres@10.96.20.57:5032/jupyterhub_db"
c.JupyterHub.template_paths = [f"{os.path.dirname(nativeauthenticator.__file__)}/templates/"]
# HTTP to HTTPS redirect
c.JupyterHub.redirect_to_server = False
c.ConfigurableHTTPProxy.command = ['configurable-http-proxy', 
                                  '--redirect-port', '8000',
                                  '--ip', '0.0.0.0']

# Use secure cookie and proxy token (take from environment)
c.JupyterHub.cookie_secret = os.environ['JUPYTERHUB_COOKIE_SECRET']
c.ConfigurableHTTPProxy.auth_token = os.environ['CONFIGPROXY_AUTH_TOKEN']
c.ConfigurableHTTPProxy.check_running_interval = 3000
# Use secure cookies
c.JupyterHub.cookie_options = {"secure": True}

# Use Native Authenticator to handle user authentication with passwords
#c.JupyterHub.authenticator_class = 'nativeauthenticator.NativeAuthenticator'
c.JupyterHub.authenticator_class = 'native'
#c.JupyterHub.authenticator_class = 'firstuseauthenticator.FirstUseAuthenticator'

# Enable password encryption
c.NativeAuthenticator.check_common_password = True
c.NativeAuthenticator.minimum_password_length = 10

# Add admin users
#c.NativeAuthenticator.admin_users = {'admin'}
#c.NativeAuthenticator.allowed_users = {'rrktsadmin'}
c.Authenticator.allowed_users = {'rrktsadmin'}
c.Authenticator.admin_users = {'rrktsadmin'}
# Set whether users need admin approval to login after signup
c.NativeAuthenticator.open_signup = True  # Require admin approval for new users

# Allow users to change their password
#c.NativeAuthenticator.allow_password_change = True

# Configure user creation
c.NativeAuthenticator.enable_signup = True

# Spawn with Docker
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'

# Spawn containers from this image
c.DockerSpawner.name_template = 'notebook-{username}'
c.DockerSpawner.image = 'jupyter-scipy-notebook:latest'

# Connect containers to this Docker network
c.DockerSpawner.network_name = os.environ.get('DOCKER_NETWORK_NAME')
c.DockerSpawner.use_internal_ip = True
#c.SwarmSpawner.host_ip = '127.0.0.1'

# Set notebook directory
notebook_dir = '/home/jovyan/work'

c.DockerSpawner.notebook_dir = notebook_dir

# Mount the user's Docker volume for data persistence
# This is the key to data persistence - Docker named volumes persist even when containers are removed
c.DockerSpawner.volumes = {
    'jupyterhub-notebook-data-{username}': notebook_dir
}

# User containers will connect to JupyterHub container
#c.DockerSpawner.hub_ip_connect = 'jupyterhub'
#c.JupyterHub.hub_ip_connect = os.environ.get('HUB_IP', 'jupyterhub')
#c.DockerSpawner.hub_ip_connect = os.environ.get('HUB_IP', 'jupyterhub')
c.DockerSpawner.debug = True
# Secure the connection between the hub and notebook servers
#c.DockerSpawner.hub_connect_url = 'http://jupyterhub:6043'

# Set container environment variables
c.DockerSpawner.environment = {
    'JUPYTER_ENABLE_LAB': '1',  # Enable JupyterLab
    'HTTPS': 'on'  # Tell the notebook servers that HTTPS is being used
}

# Remove containers when they're shut down
# Data is still preserved in the Docker volume even though containers are removed
c.DockerSpawner.remove = True

# Set resource limits (customize as needed)
#c.Spawner.cpu_limit = 2
#c.Spawner.mem_limit = 4294967296  # 4GB in bytes

# Set timeouts
c.Spawner.http_timeout = 60
c.Spawner.start_timeout = 180

# Allow users to specify their own additional pip packages
c.DockerSpawner.args = ['--NotebookApp.allow_environment_override=True']

# Security headers
c.JupyterHub.tornado_settings = {
    'headers': {
        'Content-Security-Policy': "frame-ancestors 'self'; default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'",
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
    },
    'cookie_options': {
        'httponly': True,
        'secure': True,
    },
}
# Set role for shutdown user idle session (exclude admin and poweracct)
c.JupyterHub.load_groups = {
    'admin': ['rrktsadmin','poweracct'],
    'user': ['pyuser'],
}

c.JupyterHub.load_roles = [
    {
        "name": "jupyterhub-idle-culler-role",
        "scopes": [
            "list:users",
            "read:users:activity",
            "read:servers",
            "delete:servers!group=user",
            #"admin:users", # if using --cull-users
        ],
        # assignment of role's permissions to:
        "services": ["jupyterhub-idle-culler-service"],
    }
]

c.JupyterHub.services = [
    {
        'name': 'jupyterhub-idle-culler-service',
        'command': [
            sys.executable, '-m', 'jupyterhub_idle_culler',
	    '--timeout=3600',
	    #'--cull-users'
	    #'--cull-admin-users=False'
	    '--max-age=0' #shutdown session after 12hour
        ],
    }
]

c.JupyterHub.active_server_limit = 3
c.JupyterHub.concurrent_spawn_limit = 5

# Optional: Define a hook to run when a server is spawned
def pre_spawn_hook(spawner):
    """Called after a user's server is started."""
    username = spawner.user.name
    if username == 'poweracct':
        spawner.cpu_limit = 8
        spawner.mem_limit = 34359738368  # 32GB in bytes
    else:
        spawner.cpu_limit = 6
        spawner.mem_limit = 17179869184  # 16GB in bytes
# Could add custom logic here, such as copying welcome files
    # or setting up user environment
c.Spawner.pre_spawn_hook = pre_spawn_hook
