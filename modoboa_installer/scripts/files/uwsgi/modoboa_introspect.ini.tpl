[uwsgi]
uid = %app_user
gid = %app_user
plugins = %uwsgi_plugin
home = %app_venv_path
chdir = %app_instance_path
module = instance.wsgi:application
master = true
processes = %nb_introspection_processes
vhost = true
no-default-app = true
socket = %uwsgi_socket_path
chmod-socket = 660
vacuum = true
single-interpreter = True
max-requests = 5000
buffer-size = 8192
# Serves the OAuth2 introspection endpoint only: a request is a single
# SQL query, never keep a worker longer
harakiri = 10
