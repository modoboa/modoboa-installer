[uwsgi]
uid = %modoboa_user
gid = %modoboa_user
plugins = python
home = %modoboa_venv_path
chdir = %modoboa_instance_path
module = instance.wsgi:application
master = true
harakiri = 60
processes = %nb_processes
vhost = true
no-default-app = true