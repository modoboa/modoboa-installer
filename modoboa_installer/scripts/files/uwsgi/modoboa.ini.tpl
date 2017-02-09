[uwsgi]
uid = %app_user
gid = %app_user
plugins = python
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
