IMAGE = k8scat/email-canal:latest

start:
	docker-compose up -d

build-image:
	docker build -t $(IMAGE) .

.PHONY: start build-image
