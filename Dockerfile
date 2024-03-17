FROM python:3.13.0a5-alpine
LABEL maintainer="K8sCat <k8scat@gmail.com>"
LABEL homepage="https://github.com/k8scat/email-canal"
ENV TZ=Asia/Shanghai \
    PYTHONPATH=/opt/email-canal
WORKDIR /opt/email-canal
COPY . .
RUN apk update --no-cache \
  && apk add --no-cache gcc musl-dev \
  && pip install -U pip \
  && pip install -r requirements.txt \
  && apk del gcc musl-dev
ENTRYPOINT ["python", "canal/main.py"]
