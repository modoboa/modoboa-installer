CREATE OR REPLACE FUNCTION merge_quota() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.messages < 0 OR NEW.messages IS NULL THEN
    -- ugly kludge: we came here from this function, really do try to insert
    IF NEW.messages IS NULL THEN
      NEW.messages = 0;
    ELSE
      NEW.messages = -NEW.messages;
    END IF;
    return NEW;
  END IF;

  LOOP
    UPDATE admin_quota SET bytes = bytes + NEW.bytes,
      messages = messages + NEW.messages
      WHERE username = NEW.username;
    IF found THEN
      RETURN NULL;
    END IF;

    BEGIN
      IF NEW.messages = 0 THEN
        RETURN NEW;
      ELSE
        NEW.messages = - NEW.messages;
        return NEW;
      END IF;
    EXCEPTION WHEN unique_violation THEN
      -- someone just inserted the record, update it
    END;
  END LOOP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS mergequota ON admin_quota;
CREATE TRIGGER mergequota BEFORE INSERT ON admin_quota
   FOR EACH ROW EXECUTE PROCEDURE merge_quota();
