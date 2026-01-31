FROM python:3.12
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev && apt-get clean
COPY requirements.txt .
RUN python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN apt-get install -y supervisor
COPY . .
COPY private.key /usr/server/private.key
COPY certificate.crt /usr/server/certificate.crt
EXPOSE 443
EXPOSE 8000
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]