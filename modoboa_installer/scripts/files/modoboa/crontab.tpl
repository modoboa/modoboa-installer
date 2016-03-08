#
# Modoboa specific cron jobs
#
PYTHON=%{venv_path}/bin/python
INSTANCE=%{instance_path}

# Operations on mailboxes
*       *       *       *       *       %{dovecot_mailboxes_owner}   $PYTHON $INSTANCE/manage.py handle_mailbox_operations

# Sessions table cleanup
0       0       *       *       *       root    $PYTHON $INSTANCE/manage.py clearsessions

# Logs table cleanup
0       0       *       *       *       root    $PYTHON $INSTANCE/manage.py cleanlogs

# Quarantine cleanup
%{amavis_enabled}0       0       *       *       *       root    $PYTHON $INSTANCE/manage.py qcleanup

# Notifications about pending release requests
%{amavis_enabled}0       12      *       *       *       root    $PYTHON $INSTANCE/manage.py amnotify --baseurl='http://%{hostname}'

# Logs parsing
*/5    *       *       *       *       root    $PYTHON $INSTANCE/manage.py logparser &> /dev/null

# Radicale rights file
%{radicale_enabled}*/2    *       *       *       *        root    $PYTHON $INSTANCE/manage.py generate_rights
