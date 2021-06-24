from django.core import serializers
from django.shortcuts import render, redirect
from django.db.models.expressions import RawSQL
from .models import *
from .forms import RangeInput
from django.views import View
from .forms import ModuleForm, searchForm
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from NLP.PREPROCESSING.preprocessor import Preprocessor
from NLP.PREPROCESSING.module_preprocessor import ModuleCataloguePreprocessor
from NLP.SVM.sdg_svm import SdgSvm

import pyodbc, json, os, csv
import pymongo
import pickle
from io import BytesIO, StringIO
import base64
from bson import json_util
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

import io
from colorsys import hsv_to_rgb
import numpy as np


import time, json

svm_context = {"data": None, "Predicted": None, "form": {"Default Preprocessor": "selected", "UCL Module Catalogue Preprocessor": ""}}
Module_CSV_Data, Publication_CSV_Data = None, None
global_context = {}
UCL_AffiliationID = "60022148"
lda_threshold, svm_threshold, global_display_limit = 30, 30, 150

def app(request):
    global Module_CSV_Data
    global Publication_CSV_Data
    global global_context

    all_modules = Module.objects.all()[:global_display_limit]
    all_publications = Publication.objects.all()[:global_display_limit]

    if request.method == "POST":
        updatePublicationsFromMongoDB(request)
        updateModuleData(request)
        return redirect('app')

    form = {"modBox": "unchecked", "pubBox": "unchecked", "ASC": "selected", "DESC": ""}
    len_mod = Module.objects.count()
    len_pub = Publication.objects.count()
    context = {
        'mod': all_modules,
        'pub': all_publications,
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form
    }
    
    if request.method == 'GET':
        query = request.GET.get('q')
        form = getCheckBoxState(request, form)
        if query is not None and query != '' and len(query) != 0:
            c = returnQuery(request, form, query, all_modules, all_publications)
            return render(request, 'index.html', c)
        else:
            Module_CSV_Data = None
            Publication_CSV_Data = None

    len_mod = Module.objects.count()
    len_pub = Publication.objects.count()
    context = {
        'mod': all_modules,
        'pub': all_publications,
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form
    }
    Module_CSV_Data = None
    Publication_CSV_Data = None
    global_context = context
    return render(request, 'index.html', context)

def create_bubble(contents):
    for i in contents:
        if len(contents[i]['list_of_people']) != 0:
            list_of_ppl = str(contents[i]['list_of_people']).replace('[', '').replace(']', '').replace(' ', '')
            temp = i.replace('(', '').replace(')', '')
            elem = tuple(map(int, temp.split(', ')))
            # print(elem, elem[0], elem[1], type(elem))
            # print(list_of_ppl)
            obj, created = Bubble.objects.get_or_create(
                coordinate_approach_id=elem[0],
                coordinate_speciality_id=elem[1],
                color=contents[i]['color'],
                list_of_people=list_of_ppl.replace('\'', '')
            )

def update_bubble_chart_data(request):
    status_list = Status.objects.all()
    approach_list = Approach.objects.all()
    specialty_list = Specialty.objects.all()
    colors = Color.objects.all()

    with open('data.json') as json_file:
        data = json.load(json_file)
    
    new_bubble = {}

    print("STARTED SYNC")

    for i in approach_list:
        for j in specialty_list:
            new_bubble[str((i.id, j.id))] = {}
            new_bubble[str((i.id, j.id))]['color'] = j.color
            new_bubble[str((i.id, j.id))]['list_of_people'] = []

    for i in data:
        if i['model'] == 'digitalhealth.userprofile':
            email = i['pk']
            approach = i['fields']['approach']
            speciality = i['fields']['specialty']

            for app in approach:
                for spe in speciality:
                    new_bubble[str((app, spe))]['list_of_people'].append(email)
    create_bubble(new_bubble)

def bubble_chart(request):
    # if request.method == "POST":
    #     update_bubble_chart_data(request)
    t0 = time.time()

    approach_list = Approach.objects.all()
    specialty_list = Specialty.objects.all()
    colors = Color.objects.all()
    bubbles = Bubble.objects.all()
    
    approachNum = approach_list.count()
    specialtyNum = specialty_list.count()

    color_dict = {}
    approach_dict = {}
    bubble_dict = {}

    numSpecialty, numApproach = 0, 0
    
    # t1 = time.time()-t0
    # print(t1)
    for color in colors:
        specialty_dict = {}
        for specialty in specialty_list.filter(color=color):
            specialty_dict[specialty] = numSpecialty
            numSpecialty += 1
        color_dict[color] = specialty_dict

    # t2 = time.time()-t1
    # print(t2)
    for approach in approach_list:
        approach_dict[approach] = numApproach
        numApproach += 1

    # t3 = time.time()-t2
    # print(t3)


    const_1 = 45
    case = {
        # num_of_researchers: [left, top, bubble_size]
        1: [13, 11, 9],
        2: [12, 10, 12],
        3: [11, 8, 15],
        4: [9, 7, 18],
        5: [8, 5, 21],
        6: [6, 4, 24],
        7: [4, 3, 27],
        8: [3, 2, 30],
        9: [1, 2, 33],
        10:[1, -1, 36],
        11: [-2, -2, 39],
        12: [-3, -4, 42]
    }

    for bubble in bubbles:
        specialty_index = color_dict[bubble.color][bubble.coordinate_speciality]
        approach_index = approach_dict[bubble.coordinate_approach]  
        areaNum = bubble.list_of_people.count(',') + 1

        if areaNum not in case: bubbleList = [(specialty_index * const_1)-4, (approach_index * const_1)-5, 45]
        else: bubbleList = [case[areaNum][0] + (specialty_index * const_1), case[areaNum][1] + (approach_index * const_1), case[areaNum][2]]
 
        # else: bubbleList = case[areaNum]
        bubble_dict[bubble] = bubbleList
        
    context = {'bubble_dict': bubble_dict, 'approach_dict': approach_dict,
               'color_dict': color_dict, 'verticalLength': approachNum + 1, 'horizontalLength': specialtyNum + 1}

    t4 = time.time()-t0
    print(t4)
    return render(request, 'bubble_chart.html', context)
    
def searchBubble(request, pk=None, pk_alt=None):
    obj = Bubble.objects.get(coordinate_approach=pk, coordinate_speciality=pk_alt)
    list_of_emails = obj.list_of_people.split(',')
    entry_list = [UserProfile.objects.get(email=i) for i in list_of_emails]
    return render(request, 'searchBubble.html', {"entry_list": entry_list})
    
def getDB():
    # SERVER LOGIN DETAILS
    server = 'summermiemieservver.database.windows.net'
    database = 'summermiemiedb'
    username = 'miemie_login'
    password = 'e_Paswrd?!'
    driver = '{ODBC Driver 17 for SQL Server}'
    # CONNECT TO DATABASE
    myConnection = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    curr = myConnection.cursor()
    curr.execute("SELECT * FROM [dbo].[ModuleData]")
    result = curr.fetchall()
    return result

def updateModuleData(request):
    new_data = getDB()
    for i in new_data:
        obj, created = Module.objects.get_or_create(Department_Name=i[0], Department_ID=i[1], Module_Name=i[2], Module_ID=i[3], Faculty=i[4], Credit_Value=i[5], Module_Lead=i[6], Catalogue_Link=i[7], Description=i[8])

def clearEmptySDG_assignments():
    Publication.objects.filter(assignedSDG__isnull=True).delete()

def updatePublicationsFromMongoDB(request):
    client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.hw8fo.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    db = client.Scopus
    col = db.Data
    data = col.find(batch_size=10)
    c = 0
    for i in data:
        i = json.loads(json_util.dumps(i))
        obj, created = Publication.objects.get_or_create(title=i['Title'])
        obj.title = i['Title']
        obj.data = i
        obj.save()
        c += 1
        print("Loaded", c, "/", "25830", i["DOI"])
    client.close()

def getCheckBoxState(request, form):
    # For SDG section, function reused (checkboxes and drop-down menu)
    form['Default'] = "selected" if request.GET.get('sorting') == "Default" else "unselected"
    form['ASC'] = "selected" if request.GET.get('sorting') == "ASC" else "unselected"
    form['DESC'] = "selected" if request.GET.get('sorting') == "DESC" else "unselected"

    # For main page checkboxes
    form['modBox'] = "checked" if request.GET.get('modBox') == "clicked" else "unchecked"
    form['pubBox'] = "checked" if request.GET.get('pubBox') == "clicked" else "unchecked"
    form['iheBox'] = "checked" if request.GET.get('iheBox') == "clicked" else "unchecked"

    return form

def moduleSearch(request, query, all_publications, form):
    lookups = Q(Department_Name__icontains=query) | Q(Department_ID__icontains=query) | Q(Module_Name__icontains=query) | Q(Module_ID__icontains=query) | Q(
        Faculty__icontains=query) | Q(Module_Lead__icontains=query) | Q(Description__icontains=query)
    myFilter = Module.objects.filter(lookups).distinct()
    len_mod = myFilter.count()
    len_pub = Publication.objects.count()
    return {
        'mod': myFilter,
        'pub': all_publications,
        'submitbutton': request.GET.get('submit'),
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form
    }

def publicationSearch(request, query, all_modules, form):
    myFilter = Publication.objects.filter(data__icontains=query).distinct()
    len_mod = Module.objects.count()
    len_pub = myFilter.count()
    return {
        'mod': all_modules,
        'pub': myFilter,
        'submitbutton': request.GET.get('submit'),
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form
    }

def allSearch(request, query, all_modules, all_publications, form):
    moduleResults = moduleSearch(request, query, all_modules, form)['mod']
    publicationResults = publicationSearch(request, query, all_modules, form)['pub']
    len_mod = moduleResults.count()
    len_pub = publicationResults.count()
    return {
        'mod': moduleResults,
        'pub': publicationResults,
        'submitbutton': request.GET.get('submit'),
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form
    }

def returnQuery(request, form, query, all_modules, all_publications):
    global Module_CSV_Data
    global Publication_CSV_Data
    global global_context

    if form['modBox'] == "checked" and form['pubBox'] == "unchecked":  # if only modules
        context = moduleSearch(request, query, all_publications, form)
        Module_CSV_Data = context["mod"]
        Publication_CSV_Data = None
    if form['modBox'] == "unchecked" and form['pubBox'] == "checked": # if only publications
        context = publicationSearch(request, query, all_modules, form)
        Module_CSV_Data = None
        Publication_CSV_Data = context["pub"]
    elif form['modBox'] == "checked" and form['pubBox'] == "checked":  # if both
        context = allSearch(request, query, all_modules, all_publications, form)
        Module_CSV_Data = context["mod"]
        Publication_CSV_Data = context["pub"]
    elif form['iheBox'] == "checked" and form['pubBox'] == "unchecked":
        context = publicationSearch(request, query, all_modules, form)
        Module_CSV_Data = None

    global_context = context
    return context

def iheVisualisation(request):
    return render(request, "visualisations/IHE/pyldavis.html", {})

def sdgVisualisation(request):
    return render(request, "visualisations/SDG/pyldavis.html", {})

def join(request):
    if request.method == "POST":
        form = ModuleForm(request.POST or None)
        if form.is_valid():
            form.save()
        else:
            saved_data = {
                "Department_Name": request.POST['Department_Name'],
                "Department_ID": request.POST['Department_ID'],
                "Module_Name": request.POST['Module_Name'],
                "Module_ID": request.POST['Module_ID'],
                "Faculty": request.POST['Faculty'],
                "Credit_Value": request.POST['Credit_Value'],
                "Module_Lead": request.POST['Module_Lead'],
                "Catalogue_Link": request.POST['Catalogue_Link'],
                "Description": request.POST['Description']
            }
            messages.success(request, ("There was an error in your form! Please try again."))
            return render(request, 'join.html', saved_data)

        messages.success(request, ("Your form has been submitted successfully!"))
        return redirect('app')

    else:
        return render(request, 'join.html', {})

def processForSDG(doi_searched):
    publicationData = pd.DataFrame(columns=['DOI', 'Description'])
    p = Publication.objects.all()
    for i in p:
        data = json.dumps(i.data)
        data = json.loads(data)
        doi = data['DOI']
        if doi_searched == doi:
            concatDataFields = i.title
            if data['Abstract']:
                concatDataFields += data['Abstract']
            if data['AuthorKeywords']:
                concatDataFields += " ".join(data['AuthorKeywords'])
            if data['IndexKeywords']:
                concatDataFields += " ".join(data['IndexKeywords'])
            if data['SubjectAreas']:
                subjectName = [x[0] for x in data['SubjectAreas']]
                concatDataFields += " ".join(subjectName)
            rowDataFrame = pd.DataFrame([[doi, concatDataFields]], columns=publicationData.columns)
            publicationData = publicationData.append(rowDataFrame, verify_integrity=True, ignore_index=True)
    return publicationData

def pseudocolor(val, minval, maxval):
    h = (float(val-minval) / (maxval-minval)) * 120
    r, g, b = hsv_to_rgb(h/360, 1., 1.)
    oldRange = 1
    newRange = 255
    r = int(((r) * newRange / oldRange))
    g = int(((g) * newRange / oldRange))
    b = int(((b) * newRange / oldRange))
    return r, g, b

def getModule_validation(module):
    # client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.hw8fo.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    # db = client.Scopus
    # col = db.ModuleValidation

    files_directory = "ALL_SCAPERS/moduleValidationSDG.json"
    with open(files_directory) as json_file:
        data_ = json.load(json_file)
        if module in data_:
            similarityRGB = data_[module]['Similarity']
            data_[module]['ColorRed'], data_[module]['ColorGreen'], data_[module]['ColorBlue'] = pseudocolor(similarityRGB*100, 0, 100)
            data_[module]['StringCount'] = normalise(data_[module]['SDG_Keyword_Counts'])
            
            return data_[module]

def getPublication_validation(data_, publication):
    # client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.hw8fo.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    # db = client.Scopus
    # col = db.ScopusValidation

    similarityRGB = data_[publication]['Similarity']
    data_[publication]['ColorRed'], data_[publication]['ColorGreen'], data_[publication]['ColorBlue'] = pseudocolor(similarityRGB*100, 0, 100)
    data_[publication]['StringCount'] = normalise(data_[publication]['SDG_Keyword_Counts'])
    return data_[publication]

def getThreshold(result, threshold):
    validPerc = []
    for i in range(len(result)):
        if result[i] >= threshold:
            validPerc.append(str(i + 1))
    return validPerc

def getIHE_predictions(data_, publication):
    result = [0] * 9
    lst = data_['Document Topics'][publication]
    for i in lst:
        cleaner = i.replace("(", "").replace(")", "").replace("%", "").split(',')
        topic_num = int(cleaner[0])
        percentage = float(cleaner[1])
        result[topic_num - 1] = percentage
    
    validPerc = getThreshold(result, lda_threshold)
    validPerc = ",".join(validPerc)
    return result, validPerc

def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def getSVM_predictions(data, element):
    result_array = [0] * 18
    validPerc = ""

    if element in data:
        for i in range(len(data[element])):
            if isinstance(data[element][i], float):
                weight = truncate(data[element][i] * 100, 1)
            else:
                weight = truncate(float(data[element][i]) * 100, 1)
            result_array[i] = weight

        validPerc = getThreshold(result_array, svm_threshold)
        validPerc = ",".join(validPerc)
    return result_array, validPerc

def loadSDG_Data_PUBLICATION():
    files_directory = "ALL_SCAPERS/iheScopusPrediction.json"
    with open(files_directory) as json_file:
        ihePrediction = json.load(json_file)
    files_directory = "ALL_SCAPERS/scopusValidationSDG.json"
    with open(files_directory) as json_file:
        scopusValidation = json.load(json_file)
    files_directory = "ALL_SCAPERS/svm_sdg_predictions.json"
    with open(files_directory) as json_file:
        svm_predictions = json.load(json_file)

    files_directory = "ALL_SCAPERS/scopusPrediction.json"
    publication_SDG_assignments = {}
    with open(files_directory) as json_file:
        data_ = json.load(json_file)
        count = 1
        for i in data_:
            print("Writing", count, "/", "25800")
            count += 1
            publication_SDG_assignments = data_[i]
            calc_highest = []
            for j in range(18):
                try:
                    weight = float(data_[i][str(j)]) * 100
                    weight = round(weight, 2)
                    calc_highest.append((str(j), weight))
                except:
                    pass
            
            p = sorted(calc_highest, key=lambda x: x[1])
            validWeights = []
            for sdg, weight in p:
                if weight >= lda_threshold:
                    validWeights.append(sdg)
            
            publication_SDG_assignments['DOI'] = i
            publication_SDG_assignments["Validation"] = getPublication_validation(scopusValidation, i)
            publication_SDG_assignments['ModelResult'] = ",".join(validWeights)
            publication_SDG_assignments['IHE'], publication_SDG_assignments['IHE_Prediction'] = getIHE_predictions(ihePrediction, i)
            publication_SDG_assignments['SVM'], publication_SDG_assignments['SVM_Prediction'] = getSVM_predictions(svm_predictions['Publication'], i)

            if publication_SDG_assignments["Validation"]['SDG_Keyword_Counts']:
                normalised = normalise(publication_SDG_assignments["Validation"]['SDG_Keyword_Counts'])
                publication_SDG_assignments['StringResult'] = ",".join(thresholdAnalyse(normalised, threshold=lda_threshold))
                obj = Publication.objects.get(title=data_[i]['Title'])
                obj.assignedSDG = publication_SDG_assignments
                obj.save()
    # client.close()

def loadSDG_Data_MODULES():
    # client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.hw8fo.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    # db = client.Scopus
    # col = db.ModulePrediction
    # data = col.find()
    files_directory = "ALL_SCAPERS/svm_sdg_predictions.json"
    with open(files_directory) as json_file:
        svm_predictions = json.load(json_file)

    files_directory = "ALL_SCAPERS/modulePrediction.json"
    with open(files_directory) as json_file:
        data_ = json.load(json_file)['Document Topics']
        count = 1
        for module in data_:
            print("Writing", count, "/", "5576")
            weights = data_[module]
            module_SDG_assignments = {}
            module_SDG_assignments["Module_ID"] = module
            module_SDG_assignments["Validation"] = getModule_validation(module)
            w = []
            for i in range(len(weights)):
                weights[i] = weights[i].replace('(', '').replace(')', '').replace('%', '').replace(' ', '').split(',')
                sdgNum = weights[i][0]
                module_SDG_assignments[sdgNum] = float(weights[i][1])
                w.append((sdgNum, float(weights[i][1])))

            if module_SDG_assignments["Validation"]:
                module_SDG_assignments['ModelResult'] = ",".join(thresholdAnalyse(w, threshold=lda_threshold))
                normalised = normalise(module_SDG_assignments["Validation"]['SDG_Keyword_Counts'])
                module_SDG_assignments['StringResult'] = ",".join(thresholdAnalyse(normalised, threshold=lda_threshold))
                module_SDG_assignments['SVM'], module_SDG_assignments['SVM_Prediction'] = getSVM_predictions(svm_predictions['Module'], module)
                # print(module, module_SDG_assignments['StringResult'])
                obj = Module.objects.get(Module_ID=module)
                obj.assignedSDG = module_SDG_assignments
                obj.save()
            count += 1

def thresholdAnalyse(lst, threshold):
    validWeights = []
    p = sorted(lst, key=lambda x: x[1])
    for sdg, weight in p:
        if weight >= threshold:
            validWeights.append(sdg)
    return validWeights

def normalise(lst):
    result = [0]*18
    sum_ = sum(lst)
    for i in range(len(lst)):
        if sum_ != 0:
            result[i] = (str(i+1), (lst[i] / sum_) * 100)
        else:
            result[i] = (str(i+1), 0.0)
    return result

def sortSDG_results(form, obj, ascending):
    return obj.order_by('assignedSDG__Validation__Similarity') if ascending else obj.order_by('-assignedSDG__Validation__Similarity')

def sdg(request):
    form = {"modBox": "unchecked", "pubBox": "unchecked", "iheBox": "unchecked",
                "Default": "unselected", "ASC": "unselected", "DESC": "unselected"}
    context = {
        'pub': Publication.objects.filter(assignedSDG__isnull=False),
        'mod': Module.objects.filter(Description__isnull=False),
        'lenPub': Publication.objects.count(),
        'lenMod': Module.objects.count(),
        'form': form
    }

    # Update the database with new sdg assignments
    if request.method == "POST":
        loadSDG_Data_PUBLICATION()
        loadSDG_Data_MODULES()

    if request.method == 'GET':
        query = request.GET.get('b')
        context['form'] = getCheckBoxState(request, form)
        
        if query is not None and query != '' and len(query) != 0:
            context = returnQuery(request, form, query, context['mod'], context['pub'])
        
        if context['form']['ASC'] == "selected":
            context['pub'] = sortSDG_results(form, context['pub'], ascending=True)
            context['mod'] = sortSDG_results(form, context['mod'], ascending=True)
        if context['form']['DESC'] == "selected":
            context['pub'] = sortSDG_results(form, context['pub'], ascending=False)
            context['mod'] = sortSDG_results(form, context['mod'], ascending=False)

        # Record the query results numbers
        context['lenMod'] = context['mod'].count()
        context['lenPub'] = context['pub'].count()

        # for item in context['pub']:
        #     item['assignedSDG'] = item['assignedSDG'][1:-1]

            
            # item['assignedSDG'] = item['assignedSDG'][1:] + item['assignedSDG'][:]

        context['pub'] = context['pub'][:global_display_limit]
        context['mod'] = context['mod'][:global_display_limit]

    return render(request, 'sdg.html', context)

def module(request, pk):
    try:
        module = Module.objects.get(id=pk)
    except Module.DoesNotExist:
        raise ("Module does not exist")
    return render(request, 'module.html', {'mod': module})

def publication(request, pk):
    try:
        publication = Publication.objects.get(id=pk)
    except Publication.DoesNotExist:
        raise ("Publication does not exist")
    return render(request, 'publication.html', {'pub': publication})

def export_modules_csv(request):
    global Module_CSV_Data
    global global_context
    response = HttpResponse(content_type='text/csv')

    if not Module_CSV_Data:
        messages.success(request, ("No modules to export! Please try again."))
        return render(request, 'index.html', global_context)
        
    response['Content-Disposition'] = 'attachment; filename="modules.csv"'

    try:
        writer = csv.writer(response)
        writer.writerow(["Department_Name", "Department_ID", "Module_Name", "Module_ID", "Faculty", "Credit_Value", "Module_Lead", "Catalogue_Link", "Description"])
        modules = Module_CSV_Data.values_list("Department_Name", "Department_ID", "Module_Name", "Module_ID", "Faculty", "Credit_Value", "Module_Lead", "Catalogue_Link", "Description")
        for module in modules:
            writer.writerow(module)
    except:
        messages.success(request, ("No modules to export! Please try again."))
        return render(request, 'index.html', global_context)
    
    return response

def export_publications_csv(request):
    global Publication_CSV_Data
    global global_context

    response = HttpResponse(content_type='text/csv')

    if not Publication_CSV_Data:
        messages.success(request, ("No publications to export! Please try again."))
        return render(request, 'index.html', global_context)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="publications.csv"'

    try:
        writer = csv.writer(response)
        writer.writerow(["Title", "EID", "DOI", "Year", "Source", "Volume", "Issue", "Page-Start", "Page-End", "Cited By",
                         "Link", "Abstract", "Author Keywords", "Index Keywords", "Dcoument Type", "Publication Stage", "Open Access", "Subject Areas", "UCL Authors Data", "Other Authors Data"])
    except:
        messages.success(request, ("No publications to export! Please try again."))
        return render(request, 'index.html', global_context)
    
    publications = Publication_CSV_Data.values_list("data")
    for paper in publications:
        detail = json.dumps(paper)
        all_contents = json.loads(detail)[0]
        title = all_contents['Title']
        EID = all_contents['EID']
        DOI = all_contents['DOI']
        Year = all_contents['Year']
        Source = all_contents['Source']
        Volume = all_contents['Volume']
        Issue = all_contents['Issue']
        PageStart = all_contents['PageStart']
        PageEnd = all_contents['PageEnd']
        CitedBy = all_contents['CitedBy']
        Link = all_contents['Link']
        Abstract = all_contents['Abstract']
        AuthorKeywords = all_contents['AuthorKeywords']
        if AuthorKeywords:
            AuthorKeywords = ','.join(AuthorKeywords)
        IndexKeywords = all_contents['IndexKeywords']
        if IndexKeywords:
            IndexKeywords = ','.join(IndexKeywords)
        DocumentType = all_contents['DocumentType']
        PublicationStage = all_contents['PublicationStage']
        OpenAccess = all_contents['OpenAccess']
        SubjectAreas = all_contents['SubjectAreas']
        temp = []
        if SubjectAreas:
            for area in SubjectAreas:
                temp.append(area[0])
        SubjectAreas = ','.join(temp)
        AuthorData = all_contents['AuthorData']
        UCLAuthorsData = []
        OtherAuthorsData = []
        if AuthorData:
            for id_ in AuthorData:
                name = AuthorData[id_]['Name']
                affiliationID = AuthorData[id_]['AffiliationID']
                affiliationName = AuthorData[id_]['AffiliationName']
                if affiliationID  == UCL_AffiliationID:
                    if affiliationName:
                        UCLAuthorsData.append(name + "(" + affiliationName + ")")
                    else:
                        UCLAuthorsData.append(name)
                else:
                    if name and not affiliationName:
                        OtherAuthorsData.append(','.join([name, ""]))
                    if not name and not affiliationName:
                        OtherAuthorsData.append("")
                    if name and affiliationName:
                        OtherAuthorsData.append(name + "(" + affiliationName + ")")
                    
        UCLAuthorsData = ','.join(UCLAuthorsData)
        OtherAuthorsData = ','.join(OtherAuthorsData)

        writer.writerow([title, EID, DOI, Year, Source, Volume, Issue, PageStart, PageEnd, CitedBy, Link, Abstract, AuthorKeywords,
                         IndexKeywords, DocumentType, PublicationStage, OpenAccess, SubjectAreas, UCLAuthorsData, OtherAuthorsData])

    return response

def unpickle_svm_model():
    with open("NLP/SVM/model.pkl", "rb") as input_file:
        return pickle.load(input_file)

svm = unpickle_svm_model()

def make_SVM_prediction(text, processor):
    if processor == "module":
        preprocessor = ModuleCataloguePreprocessor()
    else:
        preprocessor = Preprocessor()
    predictions = svm.make_text_predictions(text, preprocessor)
    return predictions

def check_svm_processor(request, form):
    form['Default Preprocessor'] = "checked" if request.GET.get('sorting') == "Default Preprocessor" else ""
    form['UCL Module Catalogue Preprocessor'] = "checked" if request.GET.get('sorting') == "UCL Module Catalogue Preprocessor" else ""
    return form

def drawDonutChart(results):
    fig, ax = plt.subplots(figsize=(10, 7), subplot_kw=dict(aspect="equal"))
    recipe = ["SDG 1", "SDG 2", "SDG 3", "SDG 4", "SDG 5", "SDG 6",
              "SDG 7", "SDG 8", "SDG 9", "SDG 10", "SDG 11", "SDG 12",
              "SDG 13", "SDG 14", "SDG 15", "SDG 16", "SDG 17", "Misc"]
   
   
    wedges, texts = ax.pie(results, wedgeprops=dict(width=0.5), startangle=-40)
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(recipe[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y), horizontalalignment=horizontalalignment, **kw)

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    return graphic

def universal_SVM(request):
    global svm_context

    if request.method == "GET":
        svm_context['form'] = check_svm_processor(request, svm_context['form'])
        query = request.GET.get('box')
        if svm_context['form']['UCL Module Catalogue Preprocessor'] == "checked":
            preprocessor = "module"
        else:
            preprocessor = "default"
        if query and query != "":
            prediction = make_SVM_prediction(query, processor=preprocessor)[0]
            prediction_list = prediction.tolist()
            results = []
            predicted_ = []
            for i in range(len(prediction_list)):
                temp = truncate(prediction_list[i] * 100, 1)
                results.append(temp)
                if temp >= svm_threshold:
                    predicted_.append(str(i + 1))
            svm_context["data"] = results
            svm_context["Predicted"] = ','.join(predicted_)
            svm_context["graphic"] = drawDonutChart(results)

            return render(request, 'svm.html', svm_context)
        else:
            return render(request, 'svm.html', {"data": None, "Predicted": None, "form": svm_context['form'], "graphic": None})
    
    return render(request, 'svm.html', svm_context)
