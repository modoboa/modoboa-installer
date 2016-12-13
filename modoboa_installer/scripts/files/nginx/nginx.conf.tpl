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
    ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:ECDHE-RSA-AES128-GCM-SHA256:AES256+EECDH:DHE-RSA-AES128-GCM-SHA256:AES256+EDH:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256:AES256-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4";
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_verify_depth 3;
    ssl_dhparam /etc/nginx/dhparam.pem;

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