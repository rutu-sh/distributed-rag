DEFAULT_CONT_NAME=document-processor
APP_IMAGE_NAME=document-processor
DOCKER_REPO_NAME=document-processor

create-venv:
	@echo "Creating virtual environment" && \
	python3 -m venv ${CURDIR}/.venv && \
	source ${CURDIR}/.venv/bin/activate && \
	pip3 install -r ${CURDIR}/build/requirements.txt

activate-venv:
	@echo "Activating virtual environment" && \
	export PYTHONPATH="${CURDIR}/src" && \
	source ${CURDIR}/.venv/bin/activate


build-docker-context:
	@echo "Building docker context" && \
	cp -r ${CURDIR}/src ${CURDIR}/build 


clear-docker-context:
	@echo "Clearing docker context" && \
	rm -rf ${CURDIR}/build/src

.PHONY: build
build: build-docker-context
	@echo "Building app" && \
	cd ${CURDIR}/build && \
	docker build  --no-cache --platform linux/amd64,linux/arm64 -t ${APP_IMAGE_NAME}:$(TAG) . 
	$(MAKE) clear-docker-context

run:
	@echo "Running app" && \
	docker run --rm --name ${DEFAULT_CONT_NAME} \
		-p 7070:7070 \
		${APP_IMAGE_NAME}:$(TAG)

stop:
	@echo "Stopping app" && \
	docker container stop ${DEFAULT_CONT_NAME} && \
	docker container rm ${DEFAULT_CONT_NAME} 

publish: build
	@echo "Publishing app" && \
	docker tag ${APP_IMAGE_NAME}:$(TAG) ${DOCKER_REGISTRY}/$(DOCKER_REPO_NAME):$(TAG) && \
	docker tag ${APP_IMAGE_NAME}:$(TAG) ${DOCKER_REGISTRY}/$(DOCKER_REPO_NAME):latest && \
	docker push ${DOCKER_REGISTRY}/${APP_IMAGE_NAME}:$(TAG) && \
	docker push ${DOCKER_REGISTRY}/${APP_IMAGE_NAME}:latest && \
	echo "Published ${DOCKER_REGISTRY}/${APP_IMAGE_NAME}:$(TAG) successfully"


.PHONY: all
all:
	$(MAKE) build-app && \
	$(MAKE) publish


# docker run --rm --name app-test -p 8000:8000 rutush10/simple-restapi-server-py:v0.0.1