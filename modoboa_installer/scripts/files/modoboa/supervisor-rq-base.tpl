[program:modoboa-base-worker]
autostart=true
autorestart=true
command=%{venv_path}/bin/python %{home_dir}/instance/manage.py rqworker modoboa
directory=%{home_dir}
user=%{user}
redirect_stderr=true
numprocs=1
stopsignal=TERM
