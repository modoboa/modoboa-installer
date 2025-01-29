reporting {
  # Required attributes
  enabled = true; # Enable reports in general
  email = 'postmaster@%hostname'; # Source of DMARC reports
  domain = '%hostname'; # Domain to serve
  org_name = '%hostname'; # Organisation
  # Optional parameters
  #bcc_addrs = ["postmaster@example.com"]; # additional addresses to copy on reports
  report_local_controller = false; # Store reports for local/controller scans (for testing only)
  #helo = 'rspamd.localhost'; # Helo used in SMTP dialog
  #smtp = '127.0.0.1'; # SMTP server IP
  #smtp_port = 25; # SMTP server port
  from_name = '%hostname DMARC REPORT'; # SMTP FROM
  msgid_from = 'rspamd'; # Msgid format
  #max_entries = 1k; # Maxiumum amount of entries per domain
  #keys_expire = 2d; # Expire date for Redis keys
  #only_domains = '/path/to/map'; # Only store reports from domains or eSLDs listed in this map
  # Available from 3.3
  #exclude_domains = '/path/to/map'; # Exclude reports from domains or eSLDs listed in this map
  #exclude_domains = ["example.com", "another.com"]; # Alternative, use array to exclude reports from domains or eSLDs
}
