from .views import GptTestView
from django.urls import path

urlpatterns = [
    path('test/', GptTestView.as_view(), name='gpt_test'),
]

