CREATE OR REPLACE VIEW dkim AS (
  SELECT id, name as domain_name, dkim_private_key_path AS private_key_path,
          dkim_key_selector AS selector
  FROM admin_domain WHERE enable_dkim=1;
);
