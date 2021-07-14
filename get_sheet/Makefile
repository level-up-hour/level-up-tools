IMAGE_NAME := $(USER)/get-csv
FNAME := Containerfile

all: podman-build podman-test

help:
	@echo "make build - Build and locally tag a new image."
	@echo "make build-force - Use a no-cache build"
	@echo to run: podman run --rm -it \
		-v $$PWD:/workdir:z \
		-v $$PWD/credentials:/opt/gdrive/credentials:z \
		$(IMAGE_NAME)

podman-build:
	podman build -t $(IMAGE_NAME) --file=$(FNAME) .

podman-build-force:
	podman pull ubi8-minimal
	podman build -t $(IMAGE_NAME) --file=$(FNAME) --no-cache .

podman-test:
	podman image inspect $(IMAGE_NAME)
	podman run --rm $(IMAGE_NAME) --help
