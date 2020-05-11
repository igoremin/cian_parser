from django.db import models
from django.core.validators import URLValidator
from django.shortcuts import reverse


class MapParserDetails(models.Model):
    title = models.TextField(verbose_name='Заголовок')
    price = models.CharField(max_length=100, verbose_name='Цена')
    area = models.CharField(max_length=100, verbose_name='Площадь')
    floor = models.CharField(max_length=100, verbose_name='Этаж')
    address = models.TextField(verbose_name='Адресс')
    url = models.CharField(verbose_name='URL', max_length=200, unique=True)
    object_id = models.IntegerField(unique=True, db_index=True, verbose_name='ID объекта')

    class Meta:
        verbose_name = 'Объекты'
        verbose_name_plural = 'Объекты собранные из карт'

    def __str__(self):
        return f"{self.title} : {self.price} : {self.area}"

    def get_absolute_url(self):
        return reverse('', kwargs=self.pk)


class ObjectInfoDetails(models.Model):
    title = models.CharField(max_length=300, verbose_name='Название')
    is_active = models.BooleanField(verbose_name='Активно ли объявление')
    jk_name = models.TextField(verbose_name='Описание ЖК', null=True, blank=True)
    price = models.IntegerField(verbose_name='Цена', null=True, blank=True)
    price_for_m = models.IntegerField(verbose_name='Цена за квадрат', null=True, blank=True)
    phones = models.TextField(verbose_name='Телефоны', null=True, blank=True)
    address = models.TextField(verbose_name='Адресс', null=True, blank=True)
    time_to_the_subway = models.TextField(verbose_name='Время до метро или других мест', null=True, blank=True)
    params = models.TextField(verbose_name='Параметры', null=True, blank=True)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    photos = models.TextField(verbose_name='Ссылки на фотографии', null=True, blank=True)
    url = models.CharField(verbose_name='URL', max_length=200, unique=True)
    cain_id = models.IntegerField(verbose_name='ID в базе циана', unique=True, db_index=True)

    class Meta:
        verbose_name = 'Информация об объекте'
        verbose_name_plural = 'Информация по объектам'
        ordering = ['price']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('object_info_page_url', kwargs={'pk': self.pk})


class ProxyFile(models.Model):
    proxy_file = models.FileField(upload_to='proxy_file/', blank=True, verbose_name='Файл с прокси')

    class Meta:
        verbose_name = 'Прокси файл'
        verbose_name_plural = 'Прокси файл'

    def __str__(self):
        return 'Settings'

    def update(self, *args, **kwargs):
        if self.id:
            old_proxies_file = ProxyFile.objects.get(pk=self.pk).proxy_file
            if old_proxies_file:
                old_proxies_file.delete(save=False)
        super().save(*args, **kwargs)


class ResultFile(models.Model):
    result_file = models.FileField(upload_to='results_files/', blank=True, verbose_name='Файл с результатами')

    class Meta:
        verbose_name = 'Итоговый файл'
        verbose_name_plural = 'Файлы с результатами'
        ordering = ['-id']

    def __str__(self):
        return self.result_file.name.split('/')[-1]


class TargetValue(models.Model):
    target_value = models.IntegerField(verbose_name='Цель по количеству результатов')

    class Meta:
        verbose_name = 'Цель для итогового количества результатов'
        verbose_name_plural = 'Цель по количетсву для парсинга'

    def __str__(self):
        return f'Цель : {self.target_value}'


class Status(models.Model):
    pid = models.IntegerField(verbose_name='ID процесса')
    status = models.BooleanField(verbose_name='Статус парсинга', default=False)

    class Meta:
        verbose_name = 'Статус парсига'
        verbose_name_plural = 'Статус текущего парсинга'

    def __str__(self):
        return f'PID {self.pid}, status {self.status}'
