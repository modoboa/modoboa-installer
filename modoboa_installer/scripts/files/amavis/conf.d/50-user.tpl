use strict;

# General settings
#
$inet_socket_port = [9998, 10024, 10026];
$max_servers = %max_servers;

# SQL configuration
#
@lookup_sql_dsn = ( [ 'DBI:%dbengine:database=%dbname;host=%dbhost', '%dbuser', '%dbpassword' ]);
@storage_sql_dsn = @lookup_sql_dsn;
$sql_allow_8bit_address = 1;

# Quarantine methods
#
$virus_quarantine_method = 'sql:';
$spam_quarantine_method = 'sql:';
$banned_files_quarantine_method = 'sql:';
$bad_header_quarantine_method = 'sql:';

# Tag Level
$sa_tag_level_deflt =  -999;
$sa_tag2_level_deflt =  5.0;

# Discard spam
$final_spam_destiny = D_DISCARD;

# Policy banks
#
$interface_policy{'9998'} = 'AM.PDP-INET';

$policy_bank{'AM.PDP-INET'} = {
  protocol => 'AM.PDP',
  inet_acl => [qw( 127.0.0.1 )],
};

# switch policy bank to 'ORIGINATING' for mail received on port 10026:
$interface_policy{'10026'} = 'ORIGINATING';

$policy_bank{'ORIGINATING'} = {  # mail originating from our users
  originating => 1,  # indicates client is ours, allows signing
  # force MTA to convert mail to 7-bit before DKIM signing
  # to avoid later conversions which could destroy signature:
  smtpd_discard_ehlo_keywords => ['8BITMIME'],
};

1; # ensure a defined return;
