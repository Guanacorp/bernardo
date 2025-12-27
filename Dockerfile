FROM mitmproxy/mitmproxy:10.3.0

RUN pip install --no-cache-dir \
    requests \
    python-dotenv

WORKDIR /app
COPY . /app

EXPOSE 8080
EXPOSE 8081

ENTRYPOINT ["mitmweb"]
CMD ["-s", "/app/src/bernardo.py", "--listen-host", "0.0.0.0", "--web-host", "0.0.0.0", "--web-port", "8081"]
