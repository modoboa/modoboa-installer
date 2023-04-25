[program:modoboa-dkim-worker]
autostart=true
autorestart=true
command=%{venv_path}/bin/python %{home_dir}/instance/manage.py rqworker dkim
directory=%{home_dir}
user=%{dkim_user}
redirect_stderr=true
numprocs=1
stopsignal=TERM
