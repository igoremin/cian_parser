from django.shortcuts import render, get_object_or_404, redirect
from .models import ObjectInfoDetails, ProxyFile, ResultFile, TargetValue, Status
from .forms import ProxyFileForm
from .scripts import write_results_xlsx_file
from site_engine.settings import BASE_DIR
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def results(request):
    if request.user.is_authenticated:
        if request.method == 'GET' and request.is_ajax():
            if request.GET.get('status') == 'get_status':
                done_urls = ObjectInfoDetails.objects.all().count()
                target = TargetValue.objects.all()[0].target_value
                status = Status.objects.all()[0].status

                return JsonResponse(
                    {'done_urls': done_urls,
                     'status': status,
                     'parser_progress': 100 * done_urls / target},
                    status=200
                )

        elif request.method == 'GET':
            all_results = ObjectInfoDetails.objects.all()
            try:
                target = TargetValue.objects.all()[0]
            except IndexError:
                target = 'Нет'

            proc = Status.objects.all()[0]

            paginator = Paginator(all_results, 1000)
            page_number = request.GET.get('page', 1)
            page = paginator.get_page(page_number)
            is_paginator = page.has_other_pages()

            if page.has_previous():
                prev_url = '?page={}'.format(page.previous_page_number())
            else:
                prev_url = ''

            if page.has_next():
                next_url = '?page={}'.format(page.next_page_number())
            else:
                next_url = ''

            last_url = '?page={}'.format(paginator.num_pages)

            context = {
                'all_results_len': all_results.count(),
                'target': target,
                'proc': proc,
                'page_object': page,
                'is_paginator': is_paginator,
                'next_url': next_url,
                'prev_url': prev_url,
                'last_url': last_url,
            }

            return render(request, 'cian_parser/parser_results.html', context=context)

        else:
            try:
                if request.POST['create_file'] == 'YES':
                    write_results_xlsx_file()
            except KeyError:
                pass

            try:
                if request.POST['stop_parsing'] == 'YES':
                    import os
                    status = Status.objects.all()[0]
                    try:
                        os.kill(status.pid, 9)
                    except ProcessLookupError:
                        pass
                    status.status = False
                    status.save()
                    return redirect(results)
            except KeyError:
                pass

            return redirect(all_results_files)
    else:
        context = {
            'error_message': 'Пользователь должен быть авторизован!'
        }
        return render(request, 'cian_parser/parser_results.html', context=context)


def object_info_page(request, pk):
    if request.user.is_authenticated:
        if request.method == 'GET':
            obj = get_object_or_404(ObjectInfoDetails, pk=pk)
            all_photos_no_sort = obj.photos.split('; ')[:-1]
            all_photos = [photo.replace('-2', '-1') for photo in all_photos_no_sort if '-1' not in photo]

            if len(all_photos) > 0:
                first_photo = all_photos.pop(1)
                all_indicators = [i for i in range(0, len(all_photos) + 1)]
                first_indicator = all_indicators.pop(0)
            else:
                first_photo = ''
                first_indicator = ''
                all_indicators = []

            context = {
                'object': obj,
                'all_photos': all_photos,
                'first_photo': first_photo,
                'first_indicator': first_indicator,
                'all_indicators': all_indicators,
            }

            return render(request, 'cian_parser/object_page.html', context=context)
    else:
        context = {
            'error_message': 'Пользователь должен быть авторизован!'
        }
        return render(request, 'cian_parser/object_page.html', context=context)


def all_results_files(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            all_files = ResultFile.objects.all()
            context = {
                'all_files': all_files
            }
            return render(request, 'cian_parser/all_results_files.html', context=context)
    else:
        context = {
            'error_message': 'Пользователь должен быть авторизован!'
        }
        return render(request, 'cian_parser/all_results_files.html', context=context)


def new_objects_parsing_form(request):
    # Форма для начала парсинга объектов циана
    if request.method == 'GET':
        if request.user.is_authenticated:

            context = {
                'message': 'Начать парсинг?'
            }

            return render(request, 'cian_parser/new_objects_parsing_form.html', context=context)
        else:
            context = {
                'error_message': 'Пользователь должен быть авторизован!'
            }
            return render(request, 'cian_parser/new_objects_parsing_form.html', context=context)
    else:
        if request.user.is_authenticated:
            import subprocess
            settings = False
            try:
                settings = ProxyFile.objects.all()[0]
            except IndexError:
                pass

            if settings is not False:

                proc = subprocess.Popen(['python3', f'{BASE_DIR}/cian_parser/objects_parsing.py',
                                         str(settings.proxy_file.name)])
                Status.objects.all().delete()
                new_status = Status(
                    pid=proc.pid,
                    status=True
                )
                new_status.save()

        return redirect(results)


def proxy_file(request):
    if request.user.is_authenticated:
        try:
            settings = ProxyFile.objects.all()[0]
        except IndexError:
            settings = ProxyFile()
            settings.save()
        if request.method == 'GET':

            context = {
                'form': ProxyFileForm(initial={
                    'proxy_file': settings.proxy_file,
                }),
                'old_file_name': settings.proxy_file.name.split('/')[-1] if settings.proxy_file else None
            }

            return render(request, 'cian_parser/proxy_file_form.html', context)
        else:
            form = ProxyFileForm(request.POST, request.FILES)
            if form.is_valid():
                cleaned_data = form.clean()
                if cleaned_data['proxy_file']:
                    settings.proxy_file = request.FILES['proxy_file']
                    settings.update()
                else:
                    settings.save()

            return redirect(proxy_file)
    else:
        context = {
            'error_message': 'Пользователь должен быть авторизован!'
        }
        return render(request, 'cian_parser/proxy_file_form.html', context)