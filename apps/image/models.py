from django.db import models

class image(models.Model):
    image = models.ImageField(upload_to='photos/%Y/%m/%d/')
    caption = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Photo(id={self.id}, caption={self.caption})'