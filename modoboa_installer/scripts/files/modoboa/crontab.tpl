#
# Modoboa specific cron jobs
#
PYTHON=%{venv_path}/bin/python
INSTANCE=%{instance_path}
MAILTO=%{cron_error_recipient}

# Operations on mailboxes
%{dovecot_enabled}*       *       *       *       *       %{dovecot_mailboxes_owner}   $PYTHON $INSTANCE/manage.py handle_mailbox_operations

# Sessions table cleanup
0       0       *       *       *       root    $PYTHON $INSTANCE/manage.py clearsessions

# Logs table cleanup
0       0       *       *       *       root    $PYTHON $INSTANCE/manage.py cleanlogs

# Quarantine cleanup
%{amavis_enabled}0       0       *       *       *       root    $PYTHON $INSTANCE/manage.py qcleanup

# Notifications about pending release requests
%{amavis_enabled}0       12      *       *       *       root    $PYTHON $INSTANCE/manage.py amnotify

# Logs parsing
*/5     *       *       *       *       root    $PYTHON $INSTANCE/manage.py logparser &> /dev/null
0       *       *       *       *       root    $PYTHON $INSTANCE/manage.py update_statistics

# Radicale rights file
%{radicale_enabled}*/2    *       *       *       *        root    $PYTHON $INSTANCE/manage.py generate_rights

# DNSBL checks
*/30    *       *       *       *       root    $PYTHON $INSTANCE/manage.py modo check_mx

# Public API communication
%{minutes}       %{hours}       *       *       *       root    $PYTHON $INSTANCE/manage.py communicate_with_public_api

# Generate DKIM keys (they will belong to the user running this job)
%{dkim_cron_enabled}*       *       *       *       *       %{opendkim_user}    umask 077 && $PYTHON $INSTANCE/manage.py modo manage_dkim_keys
