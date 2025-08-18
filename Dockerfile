# Alpine Linux 3.13에서 Python 3.9 이미지를 기반
FROM python:3.9-alpine3.13

# 이미지를 생성한 사람의 정보를 포함하는 레이블을 추가
LABEL maintainer="seokcoding.com"

# Python 출력 버퍼링을 비활성화
ENV PYTHONUNBUFFERED 1

# 로컬 파일 시스템에서 requirements.txt 파일을 /tmp 디렉토리로 복사
COPY ./requirements.txt /tmp/requirements.txt

# 로컬 파일 시스템에서 애플리케이션 코드를 /app 디렉토리로 복사
COPY . /app

# 이미지 내부의 작업 디렉토리를 /app으로 설정
WORKDIR /app

# 8000번 포트를 노출
EXPOSE 8000

# 이미지를 빌드 할 때 'DEV' 인자가 전달되지 않으면, 기본적으로 false로 설정
ARG DEV=false

# 가상 환경을 만들고, pip를 업그레이드하고, 필요한 패키지를 설치하며, 
# 임시 디렉토리를 삭제하고, django-user라는 사용자를 추가
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

# PATH 환경 변수를 설정하여 가상 환경에 설치된 pip를 사용할 수 있도록 한다.
ENV PATH="/py/bin:$PATH"

# django-user 사용자로 전환
USER django-user

