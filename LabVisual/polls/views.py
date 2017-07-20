from django.shortcuts import render

from django.http import HttpResponse


# def index(request):
#     return HttpResponse("Hello, world. You're at the polls index.")

from django.http import JsonResponse
from sklearn import preprocessing
import MySQLdb
import numpy as np
from django.core import serializers
import codecs, json
from scipy import cluster
import pandas as pd


def index(request):
    testNum = request.GET.get('test')
    # Connect with the MySQL Server
    db = MySQLdb.connect(host='dolgi.informatik.rwth-aachen.de', port=3306, user='ldavlab_ruiming',
                         passwd='bt8VTsGH7tsXt3BS', db='ldavlab')

    # prepare a cursor object using cursor() method
    cursor = db.cursor()

    # execute SQL query using execute() method.
    cursor.execute(
        'SELECT Bewertung, IF(VerbrauchteZeit = 0, SpentTime/60, VerbrauchteZeit/60) as amount    FROM     ldavlab_ruiming.etesttries_view where      etestnr = '+testNum+' and Status = "Beendet" and SpentTime < 3600 group by Nachname')

    data = cursor.fetchall()
    db.close()

    X = np.array(data)
    data = preprocessing.scale(X)
    # print(data)
    df = pd.DataFrame([[ij for ij in i] for i in data])
    df.rename(columns={0: 'Grade', 1: 'Time'}, inplace=True);

    x = df['Time']
    y = df['Grade']

    initial = [cluster.vq.kmeans(data, i) for i in range(1, 10)]

    cent, var = initial[3]
    # use vq() to get as assignment for each obs.
    assignment, cdist = cluster.vq.vq(data, cent)
    # df = df.assign(Class=pd.Series(assignment).values)
    dn = pd.DataFrame([[ij for ij in i] for i in X])
    dn = dn.assign(Class=pd.Series(assignment).values)
    return JsonResponse(dn.to_json(orient='records'), safe= False)