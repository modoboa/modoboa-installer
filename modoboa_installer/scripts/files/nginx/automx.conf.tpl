upstream automx {
    server unix:%uwsgi_socket_path fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name %hostname;

    access_log /var/log/nginx/%{hostname}-access.log;
    error_log /var/log/nginx/%{hostname}-error.log;

    location /mail/config-v1.1.xml {
        include uwsgi_params;
        uwsgi_pass automx;
    }
}
