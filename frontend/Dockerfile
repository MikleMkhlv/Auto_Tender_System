# Используем легкий веб-сервер
FROM nginx:alpine

# Удаляем дефолтную конфигурацию Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Копируем наши HTML/JS/CSS файлы
COPY . /usr/share/nginx/html

# Копируем кастомную конфигурацию Nginx
COPY nginx.conf /etc/nginx/conf.d/