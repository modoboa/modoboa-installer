use = ["x-spam-status", "my-x-spam-score" ,"x-virus","authentication-results" ];
extended_spam_headers = false;
skip_local = false;
skip_authenticated = false;

# Write the score as a header
custom {
   my-x-spam-score = <<EOD
     return function(task, common_meta)
       local sc = common_meta['metric_score'] or task:get_metric_score()
       -- return no error
       return nil,
       -- header(s) to add
       {['X-Spam-Score'] = string.format('%%.2f', sc[1])},
       -- header(s) to remove
       {['X-Spam-Score'] = 1},
       -- metadata to store
       {}
   end
EOD;
}

routines {
  x-virus {
    header = "X-Virus";
    remove = 1;
    symbols = ["CLAM_VIRUS", "JUST_EICAR"];
  }
}




