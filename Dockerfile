# ⚙️ Base: PHP 8.2 with Apache
FROM php:8.2-apache

# 🧱 Install system dependencies for PHP extensions
RUN apt-get update && apt-get install -y \
    libzip-dev \
    zip \
    unzip \
    libonig-dev \
    && docker-php-ext-configure zip \
    && docker-php-ext-install zip mbstring

# 🛠️ Enable Apache modules
RUN a2enmod rewrite headers

# 🔒 Harden Apache headers
RUN echo "ServerSignature Off" >> /etc/apache2/apache2.conf && \
    echo "ServerTokens Prod" >> /etc/apache2/apache2.conf && \
    echo "Header set X-Content-Type-Options nosniff" >> /etc/apache2/apache2.conf && \
    echo "Header always unset X-Powered-By" >> /etc/apache2/apache2.conf && \
    echo "Header always set X-Frame-Options DENY" >> /etc/apache2/apache2.conf && \
    echo "Header always set X-XSS-Protection \"1; mode=block\"" >> /etc/apache2/apache2.conf

# 🔐 Only copy secure files if they exist locally
# COPY payload_core.b64 /opt/secure_payload/
# COPY tokens.json /opt/secure_payload/
# COPY encryption_utils.php /opt/secure_payload/

# 📁 Move rest of project
COPY . /var/www/html/

# 🚫 Clean up and secure
RUN rm -rf /var/www/html/.git* /var/www/html/*.log /var/www/html/*.bak /var/www/html/*~ \
    && chown -R www-data:www-data /var/www/html \
    && chmod -R 750 /var/www/html

# 🔁 Optional .htaccess security
RUN touch /var/www/html/.htaccess && \
    echo "Options -Indexes" >> /var/www/html/.htaccess && \
    echo "RewriteEngine On" >> /var/www/html/.htaccess

# Increase PHP memory limit
RUN echo "memory_limit=1024M" > /usr/local/etc/php/conf.d/memory-limit.ini



# 📍 Working directory
WORKDIR /var/www/html

# 🚪 Render requires port 10000
EXPOSE 10000
RUN sed -i 's/80/10000/g' /etc/apache2/ports.conf /etc/apache2/sites-enabled/000-default.conf

# 🚀 Launch Apache in foreground
CMD ["apache2-foreground"]
