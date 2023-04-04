clamav {
  symbol = "CLAM_VIRUS";
  type = "clamav";
  servers = "127.0.0.1:3310";
  patterns {
    # symbol_name = "pattern";
    JUST_EICAR = '^Eicar-Test-Signature$';
  }
}


