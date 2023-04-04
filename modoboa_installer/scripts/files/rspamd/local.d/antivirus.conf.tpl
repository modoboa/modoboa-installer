clamav {
  scan_mime_parts = true;
  scan_text_mime = true;
  scan_image_mime = true;

  symbol = "CLAM_VIRUS";
  type = "clamav";
  servers = "/var/run/clamd.amavisd/clamd.sock";

  patterns {
    # symbol_name = "pattern";
    JUST_EICAR = "Test.EICAR";
  }
}
