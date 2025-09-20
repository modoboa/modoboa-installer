server {
    listen 80;
    listen [::]:80;
    server_name %hostname;
    root %app_instance_path;

    access_log /var/log/nginx/%{hostname}-access.log;
    error_log /var/log/nginx/%{hostname}-error.log;

    location ~ ^/(mail/config-v1.1.xml|mobileconfig) {
        include uwsgi_params;
        uwsgi_pass modoboa;
    }
}
