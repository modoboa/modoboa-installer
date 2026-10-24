# Port 80 is kept for clients when the certificate does not cover %hostname
server {
    listen 80;
    listen [::]:80;
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name %hostname autodiscover.%domain;
    root %app_instance_path;

    ssl_certificate %autoconfig_tls_cert_file;
    ssl_certificate_key %autoconfig_tls_key_file;
    ssl_protocols TLSv1.2 TLSv1.3;

    access_log /var/log/nginx/%{hostname}-access.log;
    error_log /var/log/nginx/%{hostname}-error.log;

    location ~ ^/(mail/config-v1.1.xml|mobileconfig|autodiscover/autodiscover.xml) {
        include uwsgi_params;
        uwsgi_param UWSGI_SCRIPT instance.wsgi:application;
        uwsgi_pass modoboa;
    }
}
