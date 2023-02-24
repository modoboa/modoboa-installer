-- Amavis 2.11.0 MySQL schema
-- Provided by Modoboa
-- Warning: foreign key creations are enabled

-- local users
CREATE TABLE users (
  id         int unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,  -- unique id
  priority   integer      NOT NULL DEFAULT '7',  -- sort field, 0 is low prior.
  policy_id  integer unsigned NOT NULL DEFAULT '1',  -- JOINs with policy.id
  email      varbinary(255) NOT NULL UNIQUE,
  fullname   varchar(255) DEFAULT NULL    -- not used by amavisd-new
  -- local   char(1)      -- Y/N  (optional field, see note further down)
);

-- any e-mail address (non- rfc2822-quoted), external or local,
-- used as senders in wblist
CREATE TABLE mailaddr (
  id         int unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  priority   integer      NOT NULL DEFAULT '7',  -- 0 is low priority
  email      varbinary(255) NOT NULL UNIQUE
);

-- per-recipient whitelist and/or blacklist,
-- puts sender and recipient in relation wb  (white or blacklisted sender)
CREATE TABLE wblist (
  rid        integer unsigned NOT NULL,  -- recipient: users.id
  sid        integer unsigned NOT NULL,  -- sender: mailaddr.id
  wb         varchar(10)  NOT NULL,  -- W or Y / B or N / space=neutral / score
  PRIMARY KEY (rid,sid)
);

CREATE TABLE policy (
  id  int unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
                                    -- 'id' this is the _only_ required field
  policy_name      varchar(32),     -- not used by amavisd-new, a comment

  virus_lover           char(1) default NULL,     -- Y/N
  spam_lover            char(1) default NULL,     -- Y/N
  unchecked_lover       char(1) default NULL,     -- Y/N
  banned_files_lover    char(1) default NULL,     -- Y/N
  bad_header_lover      char(1) default NULL,     -- Y/N

  bypass_virus_checks   char(1) default NULL,     -- Y/N
  bypass_spam_checks    char(1) default NULL,     -- Y/N
  bypass_banned_checks  char(1) default NULL,     -- Y/N
  bypass_header_checks  char(1) default NULL,     -- Y/N

  virus_quarantine_to      varchar(64) default NULL,
  spam_quarantine_to       varchar(64) default NULL,
  banned_quarantine_to     varchar(64) default NULL,
  unchecked_quarantine_to  varchar(64) default NULL,
  bad_header_quarantine_to varchar(64) default NULL,
  clean_quarantine_to      varchar(64) default NULL,
  archive_quarantine_to    varchar(64) default NULL,

  spam_tag_level  float default NULL, -- higher score inserts spam info headers
  spam_tag2_level float default NULL, -- inserts 'declared spam' header fields
  spam_tag3_level float default NULL, -- inserts 'blatant spam' header fields
  spam_kill_level float default NULL, -- higher score triggers evasive actions
                                      -- e.g. reject/drop, quarantine, ...
                                     -- (subject to final_spam_destiny setting)
  spam_dsn_cutoff_level        float default NULL,
  spam_quarantine_cutoff_level float default NULL,

  addr_extension_virus      varchar(64) default NULL,
  addr_extension_spam       varchar(64) default NULL,
  addr_extension_banned     varchar(64) default NULL,
  addr_extension_bad_header varchar(64) default NULL,

  warnvirusrecip      char(1)     default NULL, -- Y/N
  warnbannedrecip     char(1)     default NULL, -- Y/N
  warnbadhrecip       char(1)     default NULL, -- Y/N
  newvirus_admin      varchar(64) default NULL,
  virus_admin         varchar(64) default NULL,
  banned_admin        varchar(64) default NULL,
  bad_header_admin    varchar(64) default NULL,
  spam_admin          varchar(64) default NULL,
  spam_subject_tag    varchar(64) default NULL,
  spam_subject_tag2   varchar(64) default NULL,
  spam_subject_tag3   varchar(64) default NULL,
  message_size_limit  integer     default NULL, -- max size in bytes, 0 disable
  banned_rulenames    varchar(64) default NULL, -- comma-separated list of ...
        -- names mapped through %banned_rules to actual banned_filename tables
  disclaimer_options  varchar(64) default NULL,
  forward_method      varchar(64) default NULL,
  sa_userconf         varchar(64) default NULL,
  sa_username         varchar(64) default NULL
);


-- R/W part of the dataset (optional)
--   May reside in the same or in a separate database as lookups database;
--   REQUIRES SUPPORT FOR TRANSACTIONS; specified in @storage_sql_dsn
--
--   MySQL note ( http://dev.mysql.com/doc/mysql/en/storage-engines.html ):
--     ENGINE is the preferred term, but cannot be used before MySQL 4.0.18.
--     TYPE is available beginning with MySQL 3.23.0, the first version of
--     MySQL for which multiple storage engines were available. If you omit
--     the ENGINE or TYPE option, the default storage engine is used.
--     By default this is MyISAM.
--
--  Please create additional indexes on keys when needed, or drop suggested
--  ones as appropriate to optimize queries needed by a management application.
--  See your database documentation for further optimization hints. With MySQL
--  see Chapter 15 of the reference manual. For example the chapter 15.17 says:
--  InnoDB does not keep an internal count of rows in a table. To process a
--  SELECT COUNT(*) FROM T statement, InnoDB must scan an index of the table,
--  which takes some time if the index is not entirely in the buffer pool.
--
--        Wayne Smith adds: When using MySQL with InnoDB one might want to
--  increase buffer size for both pool and log, and might also want
--  to change flush settings for a little better performance. Example:
--    innodb_buffer_pool_size = 384M
--    innodb_log_buffer_size = 8M
--    innodb_flush_log_at_trx_commit = 0
--  The big performance increase is the first two, the third just helps with
--  lowering disk activity. Consider also adjusting the key_buffer_size.

-- provide unique id for each e-mail address, avoids storing copies
CREATE TABLE maddr (
  partition_tag integer      DEFAULT 0, -- see $partition_tag
  id         bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  email      varbinary(255)  NOT NULL,  -- full mail address
  domain     varchar(255)    NOT NULL,  -- only domain part of the email address
                                        -- with subdomain fields in reverse
  CONSTRAINT part_email UNIQUE (partition_tag,email)
) ENGINE=InnoDB;

-- information pertaining to each processed message as a whole;
-- NOTE: records with NULL msgs.content should be ignored by utilities,
--   as such records correspond to messages just being processes, or were lost
-- NOTE: instead of a character field time_iso, one might prefer:
--   time_iso TIMESTAMP NOT NULL DEFAULT 0,
--   but the following MUST then be set in amavisd.conf: $timestamp_fmt_mysql=1
CREATE TABLE msgs (
  partition_tag integer     DEFAULT 0,   -- see $partition_tag
  mail_id     varbinary(16) NOT NULL,    -- long-term unique mail id, dflt 12 ch
  secret_id   varbinary(16) DEFAULT '',  -- authorizes release of mail_id, 12 ch
  am_id       varchar(20)   NOT NULL,    -- id used in the log
  time_num    integer unsigned NOT NULL, -- rx_time: seconds since Unix epoch
  time_iso    char(16)      NOT NULL,    -- rx_time: ISO8601 UTC ascii time
  sid         bigint unsigned NOT NULL,  -- sender: maddr.id
  policy      varchar(255)  DEFAULT '',  -- policy bank path (like macro %p)
  client_addr varchar(255)  DEFAULT '',  -- SMTP client IP address (IPv4 or v6)
  size        integer unsigned NOT NULL, -- message size in bytes
  originating char(1) DEFAULT ' ' NOT NULL,  -- sender from inside or auth'd
  content     char(1),                   -- content type: V/B/U/S/Y/M/H/O/T/C
    -- virus/banned/unchecked/spam(kill)/spammy(tag2)/
    -- /bad-mime/bad-header/oversized/mta-err/clean
    -- is NULL on partially processed mail
    -- (prior to 2.7.0 the CC_SPAMMY was logged as 's', now 'Y' is used;
    -- to avoid a need for case-insenstivity in queries)
  quar_type  char(1),                   -- quarantined as: ' '/F/Z/B/Q/M/L
                                        --  none/file/zipfile/bsmtp/sql/
                                        --  /mailbox(smtp)/mailbox(lmtp)
  quar_loc   varbinary(255) DEFAULT '', -- quarantine location (e.g. file)
  dsn_sent   char(1),                   -- was DSN sent? Y/N/q (q=quenched)
  spam_level float,                     -- SA spam level (no boosts)
  message_id varchar(255)  DEFAULT '',  -- mail Message-ID header field
  from_addr  varchar(255)  CHARACTER SET utf8mb4 COLLATE utf8mb4_bin  DEFAULT '',
                                        -- mail From header field,    UTF8
  subject    varchar(255)  CHARACTER SET utf8mb4 COLLATE utf8mb4_bin  DEFAULT '',
                                        -- mail Subject header field, UTF8
  host       varchar(255)  NOT NULL,    -- hostname where amavisd is running
  PRIMARY KEY (partition_tag,mail_id),
  FOREIGN KEY (sid) REFERENCES maddr(id) ON DELETE RESTRICT
) ENGINE=InnoDB;
CREATE INDEX msgs_idx_sid      ON msgs (sid);
CREATE INDEX msgs_idx_mess_id  ON msgs (message_id); -- useful with pen pals
CREATE INDEX msgs_idx_time_num ON msgs (time_num);
-- alternatively when purging based on time_iso (instead of msgs_idx_time_num):
CREATE INDEX msgs_idx_time_iso ON msgs (time_iso);
-- When using FOREIGN KEY contraints, InnoDB requires index on a field
-- (an the field must be the first field in the index).  Hence create it:
CREATE INDEX msgs_idx_mail_id  ON msgs (mail_id);

-- per-recipient information related to each processed message;
-- NOTE: records in msgrcpt without corresponding msgs.mail_id record are
--  orphaned and should be ignored and eventually deleted by external utilities
CREATE TABLE msgrcpt (
  partition_tag integer    DEFAULT 0,    -- see $partition_tag
  mail_id    varbinary(16) NOT NULL,     -- (must allow duplicates)
  rseqnum    integer  DEFAULT 0   NOT NULL, -- recip's enumeration within msg
  rid        bigint unsigned NOT NULL,   -- recipient: maddr.id (dupl. allowed)
  is_local   char(1)  DEFAULT ' ' NOT NULL, -- recip is: Y=local, N=foreign
  content    char(1)  DEFAULT ' ' NOT NULL, -- content type V/B/U/S/Y/M/H/O/T/C
  ds         char(1)  NOT NULL,          -- delivery status: P/R/B/D/T
                                         -- pass/reject/bounce/discard/tempfail
  rs         char(1)  NOT NULL,          -- release status: initialized to ' '
  bl         char(1)  DEFAULT ' ',       -- sender blacklisted by this recip
  wl         char(1)  DEFAULT ' ',       -- sender whitelisted by this recip
  bspam_level float,                     -- per-recipient (total) spam level
  smtp_resp  varchar(255)  DEFAULT '',   -- SMTP response given to MTA
  PRIMARY KEY (partition_tag,mail_id,rseqnum),
  FOREIGN KEY (rid)     REFERENCES maddr(id)     ON DELETE RESTRICT,
  FOREIGN KEY (mail_id) REFERENCES msgs(mail_id) ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE INDEX msgrcpt_idx_mail_id  ON msgrcpt (mail_id);
CREATE INDEX msgrcpt_idx_rid      ON msgrcpt (rid);
-- Additional index on rs since Modoboa uses it to filter its quarantine
CREATE INDEX msgrcpt_idx_rs       ON msgrcpt (rs);

-- mail quarantine in SQL, enabled by $*_quarantine_method='sql:'
-- NOTE: records in quarantine without corresponding msgs.mail_id record are
--  orphaned and should be ignored and eventually deleted by external utilities
CREATE TABLE quarantine (
  partition_tag integer    DEFAULT 0,    -- see $partition_tag
  mail_id    varbinary(16) NOT NULL,     -- long-term unique mail id
  chunk_ind  integer unsigned NOT NULL,  -- chunk number, starting with 1
  mail_text  blob          NOT NULL,     -- store mail as chunks of octets
  PRIMARY KEY (partition_tag,mail_id,chunk_ind),
  FOREIGN KEY (mail_id) REFERENCES msgs(mail_id) ON DELETE CASCADE
) ENGINE=InnoDB;
