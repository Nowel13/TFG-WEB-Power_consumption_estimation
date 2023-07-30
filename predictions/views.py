from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from requests_toolbelt.multipart.encoder import MultipartEncoder
from .forms import UploadFileForm
from django.conf import settings
import requests
import os
import csv
import time
import zipfile
import numpy as np
import pandas as pd
import json


# Página principal de la web:
def index(request):
    template = loader.get_template("predictions/index.html")
    return HttpResponse(template.render({}, request))


# Subir archivos ya procesados:
# De esta forma podemos mandar los archivos ya procesados desde el front, lo que
# evita que tarde demasiado en descargarlos y enviarlos y luego en recibirlos y procesarlos.
# Al procesarlos desde aquí, los archivos que se envían ocupan 1000 veces menos espacio, por lo 
# que el envío es casi instantáneo tras procesarlos.
def upload_processed_files(request):
    n_files = get_n_files()
    context = {
        "n_files": n_files,
    }
    start = time.time()
    if request.method == 'POST':
        files = request.FILES.getlist("document")
        files_list = read_files(files)
        response = requests.post('http://127.0.0.1:8000/upload_processed_files', json=files_list)
        context["message"] = response.json()["info"]
        n_files = get_n_files()
        context["n_files"] = n_files
    finish = time.time()
    context["time"] = round(finish - start, 3)
    template = loader.get_template('predictions/uploads.html')
    return HttpResponse(template.render(context, request))


# Subir archivos sin procesar:
# Sin embargo si utilizamos MultipartEncoder, nos permite realizar el envío de
# archivos por partes, permitiendo su correcto funcionamiento:
def upload_files(request):
    n_files = get_n_files()
    context = {
        "n_files": n_files,
    }
    if request.method == 'POST':
        remove_result_files()
        files = request.FILES.getlist("document")
        m = MultipartEncoder(
            fields=[('files', (file.name, file.file)) for file in files]
        )
        response = requests.post('http://127.0.0.1:8000/upload_files', data=m, headers={'Content-Type': m.content_type})
        context["message"] = response.json()["info"]
    template = loader.get_template('predictions/uploads.html')
    return HttpResponse(template.render(context, request))


def delete(request):
    n_files = get_n_files()
    context = {
        "n_files": n_files,
    }
    if request.method == 'POST':
        response = requests.delete('http://127.0.0.1:8000/delete')
        context["message"] = response.text
        remove_result_files()
        n_files = get_n_files()
        context["n_files"] = n_files
    template = loader.get_template('predictions/delete.html')
    return HttpResponse(template.render(context, request))


def process_data(request):
    n_files = get_n_files()
    context = {
        "n_files": n_files,
    }
    if request.method == 'POST':
        remove_result_files()
        params = {}
        for key, value in request.POST.items():
            if key != 'csrfmiddlewaretoken':
                params[key] = value
        response = requests.get('http://127.0.0.1:8000/process', params=params)
        context["message"] = response.json()["message"]
        n_files = get_n_files()
        context["n_files"] = n_files
    template = loader.get_template('predictions/processed.html')
    return HttpResponse(template.render(context, request))


def apply_model(request):
    n_files = get_n_files()
    context = {
        "n_files": n_files,
    }
    if request.method == "POST":
        remove_result_files()
        params = {}
        for key, value in request.POST.items():
            if key != 'csrfmiddlewaretoken':
                params[key] = value
        response = requests.post('http://127.0.0.1:8000/apply_model', params=params)
        context["selected_model"] = response.json()["selected"]
        context["time"] = response.json()["time"]
    template = loader.get_template('predictions/apply_model.html')
    return HttpResponse(template.render(context, request))


def results(request):
    n_files = get_n_files()
    show_results = False
    for root_folder, folders, files in os.walk(settings.MEDIA_ROOT+"/data/results"):
        if len(files) > 0:
            show_results = True
    context = {
        "n_files": n_files,
        "show_results": show_results,
    }
    if request.method == "POST":
        remove_result_files()
        response = requests.get('http://127.0.0.1:8000/results')
        open(settings.MEDIA_ROOT + "/files.zip", "wb").write(response.content)
        with zipfile.ZipFile(settings.MEDIA_ROOT + "/files.zip", 'r') as zip_ref:
            zip_ref.extractall(settings.MEDIA_ROOT)
        for root_folder, folders, files in os.walk(settings.MEDIA_ROOT+"/data/results"):
            if len(files) > 0:
                show_results = True
    if show_results:
        archivo = open(settings.MEDIA_ROOT + '/data/results/prediction.txt', 'r')
        datos = []
        for linea in archivo.readlines():
            datos.append(linea.split())
        archivo.close()
        context["datos"] = datos
        context["show_results"] = show_results
    template = loader.get_template("predictions/results.html")
    return HttpResponse(template.render(context, request))


####################################
####### FUNCIONES AUXILIARES #######
####################################

# Get number of files already uploaded:
def get_n_files():
    return requests.get('http://127.0.0.1:8000/').json()["n_files"]

# Delete files:
def remove_file(path):
	if not os.remove(path):
		return f"{path} is removed successfully"
	else:
		return f"Unable to delete the {path}"

def remove_result_files():
    for root_folder, folders, files in os.walk(settings.MEDIA_ROOT+"/data/results"):
        for file in files:
            file_path = os.path.join(root_folder, file)
            remove_file(file_path)
    for root_folder, folders, files in os.walk(settings.MEDIA_ROOT+"/"):
        for file in files:
            file_path = os.path.join(root_folder, file)
            remove_file(file_path)

# Same method like the one on the API:
def read_files(files):
    data = []
    for file in files:
        print("Comienza el proceso del archivo: ", file.name)
        start_time = time.time()
        datos = pd.read_csv(
            file,
            sep=' ',
            header=None, 
            names=['MeterID', 'Time', 'kwh']
                        )
        datos['Time'] = np.where(datos['Time'] % 2 == 0, datos['Time'] - 1, datos['Time'])
        datos = datos.groupby(["MeterID","Time"], sort=False).agg(kwh=("kwh", "sum"), half_hours=("kwh","count")).reset_index()
        datos.loc[datos["half_hours"] == 1, "kwh"] *= 2
        datos = datos.drop(["half_hours"], axis=1)
        datos = datos.groupby("Time").agg(sum_kwh=("kwh", "sum"), count_users=("kwh","count")).reset_index()
        data.append({"filename": file.name, "dataframe": datos.to_json()})
        finish_time = time.time()
        print("Ha tardado: ", finish_time - start_time, " en procesar el archivo: ", file.name)
    return data
