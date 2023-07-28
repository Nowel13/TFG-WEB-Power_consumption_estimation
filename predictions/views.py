from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from requests_toolbelt.multipart.encoder import MultipartEncoder
from .forms import UploadFileForm
import requests

def index(request):
    template = loader.get_template("predictions/index.html")
    return HttpResponse(template.render({}, request))

def test1(request, arg):
    template = loader.get_template("predictions/test1.html")
    context = {
        "data": arg,
    }
    return HttpResponse(template.render(context, request))

def test2(request, arg):
    resp = requests.get('http://127.0.0.1:8000/')
    print(resp)
    return HttpResponse(resp)

# def upload_file(request, file):
    # ficheros = {'file1': open(file.filename, 'rb')}
    # r = requests.post('http://127.0.0.1:8000/file', files=ficheros)

# def upload(request):
#     context = {}
#     if request.method == 'POST':
#         file = request.FILES["document"]
#         response = requests.post('http://127.0.0.1:8000/file', files={'file': file})        
#     template = loader.get_template('predictions/upload.html')
#     return HttpResponse(template.render(context, request))

def uploads(request):
    context = {}
    if request.method == 'POST':
        files = request.FILES.getlist("document")
        ########################################
        # Esta forma no sirve para archivos grandes como los que tenemos de ejemplo:
        # files_dict = [
        #     ('files', file) for file in files
        # ]
        # response = requests.post('http://127.0.0.1:8000/files', files=files_dict)
        ########################################
        # Sin embargo si utilizamos MultipartEncoder, nos permite realizar el envío de
        # archivos por partes, permitiendo su correcto funcionamiento:
        m = MultipartEncoder(
            fields=[('files', (file.name, file.file)) for file in files]
        )
        response = requests.post('http://127.0.0.1:8000/files', data=m, headers={'Content-Type': m.content_type})
    template = loader.get_template('predictions/uploads.html')
    return HttpResponse(template.render(context, request))

# def upload_file(request):
#     if request.method == "POST":
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             r = requests.post('http://127.0.0.1:8000/file', files=request.FILES["file"])
#             return HttpResponse(r)
#     else:
#         form = UploadFileForm()
#     return render(request, "upload.html", {"form": form})

def process_data(request):
    context = {}
    if request.method == 'POST':
        response = requests.get('http://127.0.0.1:8000/process', params={"max_days_before": 5})
        context = {
            "n_files": response.json()["n_files"],
            "message": response.json()["message"],
        }
    template = loader.get_template('predictions/processed.html')
    return HttpResponse(template.render(context, request))

def delete(request):
    context = {}
    if request.method == 'POST':
        response = requests.delete('http://127.0.0.1:8000/delete')
        context = {
            "message": response.text,
        }
    template = loader.get_template('predictions/delete.html')
    return HttpResponse(template.render(context, request))

def apply(request):
    context = {}
    if request.method == "POST":
        response = requests.post('http://127.0.0.1:8000/apply', params={"model_name": "random_forest"})
        context = {
            "message": response.json()["selected"],
            "time": response.json()["time"],
        }
    template = loader.get_template('predictions/apply_model.html')
    return HttpResponse(template.render(context, request))

def results(request):
    response = requests.get('http://127.0.0.1:8000/results')
    print(response.json()["image"])
    context = {
        "image": response.json()["image"],
    }
    template = loader.get_template("predictions/results.html")
    return HttpResponse(template.render(context, request))
