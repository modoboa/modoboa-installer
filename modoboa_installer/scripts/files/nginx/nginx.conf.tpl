upstream modoboa {
    server unix:%uwsgi_socket_path fail_timeout=0;
}

server {
    listen 80;
    server_name %hostname;
    rewrite ^ https://$server_name$request_uri? permanent;
}

server {
    listen 443 ssl;
    server_name %hostname;
    root %modoboa_instance_path;

    ssl_certificate %tls_cert_file;
    ssl_certificate_key %tls_key_file;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers RC4:HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_verify_depth 3;

    client_max_body_size 10M;

    access_log /var/log/nginx/%{hostname}-access.log;
    error_log /var/log/nginx/%{hostname}-error.log;

    location /sitestatic/ {
        autoindex on;
    }

    location /media/ {
        autoindex on;
    }

    location / {
        include uwsgi_params;
        uwsgi_param UWSGI_SCRIPT instance.wsgi:application;
        uwsgi_pass modoboa;
    }
}