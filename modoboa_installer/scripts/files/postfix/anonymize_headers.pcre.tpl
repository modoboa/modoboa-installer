if /^\s*Received:.*Authenticated sender.*\(Postfix\)/
/^Received: from .*? \([\w\-.]* \[.*?\]\)(.*|\n.*)\(Authenticated sender: (.+)\)\s+by.+\(Postfix\) with (.*)/
  REPLACE Received: from [127.0.0.1] (localhost [127.0.0.1]) by localhost (Mailerdaemon) with $3
endif
if /^\s*Received: from .*rspamd.localhost .*\(Postfix\)/
/^Received: from.* (.*|\n.*)\((.+) (.+)\)\s+by (.+) \(Postfix\) with (.*)/
  REPLACE Received: from rspamd (rspamd $3) by $4 (Postfix) with $5
endif
/^\s*X-Enigmail/        IGNORE
/^\s*X-Originating-IP/  IGNORE
/^\s*X-Forward/         IGNORE
