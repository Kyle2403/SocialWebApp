import os
from os import listdir
from os.path import isfile, join
def readPosts():
    cur = os.getcwd()
    search_dir = "posts"
    files = [f for f in os.listdir(search_dir) if os.path.isfile(os.path.join(search_dir, f))]
    allfiles = [os.path.join(cur+"/"+search_dir, f) for f in files]
    allfiles.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    txt = []
    posts = []
    for file in allfiles:
        if "txt" in file:
            txt.append(file)
    for file in txt:
        filepath = file
        all = open(filepath ,"r")
        content = all.read()
        title = content.split("END123")[0]
        body = content.split("END123")[1]
        img_cmt = content.replace(title,"").replace(body,"").replace("END123","")
        img = img_cmt.split("COmmeNT")[0]
        cmt = img_cmt.replace(img,"").replace("COmmeNT","")
        cmt= cmt.split("COMMENT_SEPERATOR")
        cmt.remove("")
        new = []
        body = body.replace("\n","<br>")
        new.append(title)
        new.append(body)
        new.append(img)
        new.append(cmt)
        posts.append(new)
    return posts

def savePost(title,body,image):
    filename = "./posts/" + title + ".txt"
    filename = filename.replace("END123","")
    file = open(filename,"a")
    #if list(title)[len(list(title))-1]==".":
    file.write(title)
    #else:
        #file.write(title + ".")
    #if list(body)[len(list(body))-1]==".":
    file.write(body)
    #else:
        #file.write(body + ".")
    file.write(image)
    file.close()

def delPost(title):
    filename = "./posts/" + title + ".txt"
    if os.path.exists(filename):
        os.remove(filename)
        return "exists"
    else:
        return "not exist"
    
def addComment(comment, title, owner):
    filename = "./posts/" + title + ".txt"
    file = open(filename,"r")
    content = file.read()
    file.close()
    file = open(filename,"a")
    if "COmmeNT" not in content:
        file.write("COmmeNT")
    new_comment =  owner + ": " + comment + "COMMENT_SEPERATOR"
    file.write(new_comment)
    file.close()