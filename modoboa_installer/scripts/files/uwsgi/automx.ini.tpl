[uwsgi]
uid = %app_user
gid = %app_user
plugins = %uwsgi_plugin
home = %app_venv_path
chdir = %app_instance_path
module = automx_wsgi
master = true
vhost = true
harakiri = 60
processes = %nb_processes
socket = %uwsgi_socket_path
chmod-socket = 660
vacuum = true
