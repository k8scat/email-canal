IMAGE = k8scat/email-canal:latest

build-image:
	docker build -t $(IMAGE) .

.PHONY: build-image
