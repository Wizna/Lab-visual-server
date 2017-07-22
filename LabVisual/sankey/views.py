import re
import pickle
import operator
from django.http import JsonResponse

# read in students selection of courses data in march
data = pickle.load(open("sankey/coursetable_march.p", "rb"))
listforfp = list(data.values())
# thanks for your advice, after analyzing the numbers of courses map to a single ip
# I decided to use those less than 16 as valid ones after doing a exponential regression
listforfp = [item for item in listforfp if len(item) < 16]
# read in dictionary of (LVNumber, course name)
lv2name = pickle.load(open("sankey/lv2name.p", "rb"))


def index(request):
    # get list of constraint courses
    courses = request.GET.get('course')
    strarray = re.findall('[0-9]{2}\w[sS]\-[0-9]{5}', courses)
    strarray = [i.lower().replace('ws-', '1').replace('ss-', '2') for i in strarray]

    # remove duplicate ones
    queryset = set(strarray)

    # decide the popularity of courses for further sorting
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
    # make only those contains constraint course count
    for index, item in enumerate(listforfp):
        # add the check to make other connection not counting
        if queryset.issubset(item):
            temp = [int(i) for i in item if pattern.match(i)]
            newfp.append(list(set(temp) & orderedset))

    # After sorting, I am now able to construct a frequent pattern tree
    # although I actually merge all nodes with same names in the graph
    # and make it not a tree
    for item in newfp:
        item.sort(key=lambda x: orderedlist.index(x))

    # accumulate link for each adjacent pairs of courses
    dictlink = {}
    for item in newfp:
        for index, subitem in enumerate(item):
            if index != 0:
                insertLink(item[index - 1], subitem, dictlink)

    # sort links by popularity and select the most important ones
    sortedlink = sorted(dictlink.items(), key=operator.itemgetter(1), reverse=True)
    sortedlink = sortedlink[:100]

    # remove duplicate course names if there are
    # (to make nodes can be identified by course names)
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

    # prepare data in json format
    dictforjson = {}
    datajson = [{"source": lv2name[key[0]], "target": lv2name[key[1]], "value": value} for key, value in sortedlink if
                key[0] in lv2name and key[1] in lv2name]
    namejson = [{"name": lv2name[course]} for course in orderedlist if course in lv2name]
    dictforjson["nodes"] = namejson
    dictforjson["links"] = datajson

    return JsonResponse(dictforjson)


# function to accumulate links number
def insertLink(source, target, dictionary):
    indextuple = (source, target)
    if indextuple in dictionary:
        dictionary[indextuple] += 1
    else:
        dictionary[indextuple] = 1
