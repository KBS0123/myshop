import os
from celery import Celery

# Celery 프로그램에 대한 기본 장고 설정 모듈을 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
app = Celery('myshop')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()