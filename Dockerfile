FROM python:3.10.4-alpine
LABEL maintainer="K8sCat <k8scat@gmail.com>"
LABEL homepage="https://github.com/k8scat/email-canal"
ENV PROD=true \
    TZ=Asia/Shanghai
WORKDIR /opt/email-canal
COPY . .
RUN pip install -U pip \
  && pip install -r requirements.txt
ENTRYPOINT ["python", "main.py"]
