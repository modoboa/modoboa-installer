actions {
    reject = 15; # normal value is 15, 150 so it will never be rejected
    add_header = 6; # set to 0.1 for testing, 6 for normal operation.
    rewrite_subject = 8; # Default: 8
    greylist = 4; # Default: 4
}

group "antivirus" {
  symbol "JUST_EICAR" {
    weight = 10;
    description = "Eicar test signature";
  }
  symbol "CLAM_VIRUS_FAIL" {
    weight = 0;
  }
  symbol "CLAM_VIRUS" {
    weight = 10;
    description = "ClamAV found a Virus";
  }
}
