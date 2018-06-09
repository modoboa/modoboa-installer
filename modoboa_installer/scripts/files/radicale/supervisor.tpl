[program:radicale]
autostart=true
autorestart=true
command=%{venv_path}/bin/radicale -C %{config_dir}/config
directory=%{home_dir}
redirect_stderr=true
user=%{user}
numprocs=1
