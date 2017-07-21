import re
import pickle
import operator
from django.http import JsonResponse

data = pickle.load(open("sankey/coursetable_march.p", "rb"))
listforfp = list(data.values())
listforfp = [item for item in listforfp if len(item) < 26]
lv2name = pickle.load(open("sankey/lv2name.p", "rb"))


def index(request):
    courses = request.GET.get('course')
    print(courses)
    strarray = re.findall('[0-9]{2}\w[sS]\-[0-9]{5}', courses)
    strarray = [i.lower().replace('ws-', '1').replace('ss-', '2') for i in strarray]
    print(strarray)

    queryset = set(strarray)

    dictsort = {}
    for courses in listforfp:
        if queryset.issubset(courses):
            for cornum in courses:
                # check whether to accumulate on existed one or set for the first time
                if cornum in dictsort:
                    dictsort[cornum] += 1
                else:
                    dictsort[cornum] = 1

    sorted_dict = sorted(dictsort.items(), key=operator.itemgetter(1), reverse=True)
    orderedlist = [int(i[0]) for i in sorted_dict]
    # limit the number of courses considered, also remove the query courses
    orderedlist = orderedlist[:100]
    for item in queryset:
        orderedlist.remove(int(item))
    orderedset = set(orderedlist)

    pattern = re.compile('^[0-9]+$')

    newfp = []
    for index, item in enumerate(listforfp):
        # add the check to make other connection not counting
        if queryset.issubset(item):
            temp = [int(i) for i in item if pattern.match(i)]
            newfp.append(list(set(temp) & orderedset))

    for item in newfp:
        item.sort(key=lambda x: orderedlist.index(x))

    dictlink = {}
    for item in newfp:
        for index, subitem in enumerate(item):
            if index != 0:
                insertLink(item[index - 1], subitem, dictlink)

    sortedlink = sorted(dictlink.items(), key=operator.itemgetter(1), reverse=True)
    sortedlink = sortedlink[:100]

    checkDuplicate = []
    containCourse = []

    for key, value in sortedlink:
        if key[0] in lv2name:
            temp1 = lv2name[key[0]]
            if temp1 not in checkDuplicate:
                containCourse.append(key[0])
                checkDuplicate.append(temp1)

        if key[1] in lv2name:
            temp2 = lv2name[key[1]]

            if temp2 not in checkDuplicate:
                containCourse.append(key[1])
                checkDuplicate.append(temp2)

    orderedlist = list(orderedset & set(containCourse))

    sortedlink = [(key, value) for key, value in sortedlink if key[0] in orderedlist and key[1] in orderedlist]

    print(len(orderedlist))

    dictforjson = {}
    datajson = [{"source": lv2name[key[0]], "target": lv2name[key[1]], "value": value} for key, value in sortedlink if
                key[0] in lv2name and key[1] in lv2name]
    namejson = [{"name": lv2name[course]} for course in orderedlist if course in lv2name]
    dictforjson["nodes"] = namejson
    dictforjson["links"] = datajson

    print(dictforjson)
    return JsonResponse(dictforjson)


def insertLink(source, target, dictionary):
    indextuple = (source, target)
    if indextuple in dictionary:
        dictionary[indextuple] += 1
    else:
        dictionary[indextuple] = 1
