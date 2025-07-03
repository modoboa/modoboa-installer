[uwsgi]
uid = %app_user
gid = %app_user
plugins = %uwsgi_plugin
home = %app_venv_path
chdir = %app_instance_path
module = instance.wsgi:application
master = true
processes = %nb_processes
vhost = true
no-default-app = true
socket = %uwsgi_socket_path
chmod-socket = 660
vacuum = true
single-interpreter = True
max-requests = 5000
buffer-size = 8192
