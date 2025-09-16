require "fileinto";
if header :contains "X-Spam-Status" "Yes" {
    fileinto "Junk";
}
