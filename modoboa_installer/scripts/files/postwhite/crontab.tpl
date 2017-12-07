#
# Postwhite specific cron jobs
#

# Update Postscreen Whitelists
@daily   root   /usr/local/bin/postwhite/postwhite > /dev/null 2>&1

# Update Yahoo! IPs for Postscreen Whitelists
@weekly  root   /usr/local/bin/postwhite/scrape_yahoo > /dev/null 2>&1
