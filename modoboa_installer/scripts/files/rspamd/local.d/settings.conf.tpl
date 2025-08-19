authenticated {
  priority = high;
  authenticated = yes;
  apply {
    groups_disabled = ["rbl", "spf"];
  }
%{whitelist_auth_enabled}  symbols ["WHITELIST_AUTHENTICATED"];
}
