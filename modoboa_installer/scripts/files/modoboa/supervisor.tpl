[program:policyd]
autostart=true
autorestart=true
command=%{venv_path}/bin/python %{home_dir}/instance/manage.py policy_daemon
directory=%{home_dir}
redirect_stderr=true
user=%{user}
numprocs=1
