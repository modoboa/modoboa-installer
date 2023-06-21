clamav {
  scan_mime_parts = true;
  scan_text_mime = true;
  scan_image_mime = true;
  retransmits = 2;
  timeout = 30;
  symbol = "CLAM_VIRUS";
  type = "clamav";
  servers = "127.0.0.1:3310"

  patterns {
    # symbol_name = "pattern";
    JUST_EICAR = "Test.EICAR";
  }
}
