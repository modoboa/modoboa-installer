use = ["x-spam-status","x-virus","authentication-results" ];
extended_spam_headers = false;
skip_local = false;
skip_authenticated = false;

routines {
  x-virus {
    header = "X-Virus";
    remove = 1;
    symbols = ["CLAM_VIRUS", "JUST_EICAR"];
  }
}




