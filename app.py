from flask import Flask, render_template, redirect, request, session # type: ignore
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash # type: ignore

# used to connect to Heroku databse
import os
import psycopg2 # type: ignore
from psycopg2 import Error # type: ignore

# import requests for api calls
import requests
# import for choice function
import random

# importing date class from datetime module for favorites 
from datetime import date
# import for first letter caps function
import string
# import gotenv library for environment variables
from dotenv import load_dotenv, dotenv_values # type: ignore

app = Flask(__name__)

# Wipe any old and load env variables for db connection
load_dotenv(override=True)

# configure session to have a length of time for timeout after being signed in / setup filesystem for session files
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# set up login required function / wrapper
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(session)
        if session.get("name") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["POST", "GET"])
def homepage():
    session.clear()
    print(session)
    if request.method == "POST":
        # if user selects register button show register page
        if request.form.getlist("register") != None and request.form.getlist("register") != []:
            return redirect("/register")
        # if user selects login button show login page
        if request.form.getlist("login") != None:
            return redirect("/login")

    return render_template("homepage.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    session.clear()
    # if user sends input to form add new user to database
    if request.method == "POST":
        if request.form.getlist("newlogin") != None and request.form.getlist("newlogin") != []:
            return redirect("/login")
        if not request.form.get("username"):
            return render_template("register.html")
        if not request.form.get("password"):
            return render_template("register.html")
        if not request.form.get("password2"):
            return render_template("register.html")
        # check for invalid symbols
        if "'" in (request.form.get("username")) or ";" in (request.form.get("username")):
            return render_template("registerinvalid.html")
        if "'" in (request.form.get("password")) or ";" in (request.form.get("password")):
            return render_template("registerinvalid.html")
        if "'" in (request.form.get("password2")) or ";" in (request.form.get("password2")):
            return render_template("registerinvalid.html")

        # check if password and verify password entries match 
        if request.form.get("password") == request.form.get("password2"):
            try:
                # Connect to hosted database \ any db in .env config - previously hosted on Heroku
                connection = connectdb()
                # Create a cursor to perform database operations
                cursor = connection.cursor()
                # Get current username input from user
                username = request.form.get("username")
                # Get / check usernames already created / stored in db
                cursor.execute("""SELECT username FROM users;""")
                usernames = cursor.fetchall()
                print(username)
                print(usernames)
                if (username,) in usernames:
                    print("testtest")
                    return render_template("registeruserexists.html")
                # if user does not already exist in db - add new user into table 
                username = request.form.get("username")
                passwordhash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
                cursor.execute("""INSERT INTO users (username, passwordhash) VALUES (%s, %s);""", (username, passwordhash))
                connection.commit()
            
                

            except (Exception, Error) as error:
                print("Error while connecting to PostgreSQL", error)

            finally:
                if (connection):
                    cursor.close()
                    connection.close()
                    print("PostgreSQL connection is closed")
            return render_template("registerloggedin.html")
    
    return render_template("register.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    session.clear()
    # if form is submitted 
    if request.method == "POST":
        userinput = request.form.get("username")
        passinput = request.form.get("password")
        # check for invalid symbols
        if "'" in userinput or ";" in userinput:
            return render_template("logininvalid.html")
        if "'" in passinput or ";" in passinput:
            return render_template("logininvalid.html")
        # store username into session
        session["name"] = request.form.get("username")

        # check if username / password submitted is users table 
        try:
                # Connect to heroku hosted database \ any db in .env config
                connection = connectdb()

                # Create a cursor to perform database operations
                cursor = connection.cursor()
                # get usernames from db
                cursor.execute("""SELECT username FROM users;""")
                username = cursor.fetchall()
                print(username)
                # get passwordhash from db for username
                cursor.execute("""SELECT passwordhash FROM users WHERE username=%s;""", (session["name"],))
                passwordhash = cursor.fetchall()
                # check if user exists in db
                if (userinput,) not in username:
                    return render_template("loginnotfound.html")
                # passwordhash returns from db as a list of tuple - index [0] [0] to get str
                # check if user password is correct
                if not check_password_hash(passwordhash[0][0], passinput):
                    return render_template("loginpassnotfound.html")
                # if username and password match db log user in
                #return redirect("/profile")
                return redirect("/getrecipe")
        except (Exception, Error) as error:
                print("Error while connecting to PostgreSQL", error)

        finally:
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
        
        
        
        # login / send to homepage if user exists
        #if (session["name"],) in username:
        #    return redirect("/layout")
    return render_template("login.html")


@app.route("/profile", methods=["POST", "GET"])
@login_required
def profile():
    if request.method == "POST":
        # if user selects new recipe after saving profile
        if request.form.getlist("newrecipe") != None and request.form.getlist("newrecipe") != []:
            return redirect("/getrecipe")
        
        print(request.form)
        # condition 1: user has never saved allergies - insert into db
        # condition 2: user has saved allergies but wants to update using save button - update db
        # get current allergy selections testing template
        #dairy = request.form.get("dairy")
        #if dairy == "":
        #    dairy = True
        #else:
        #    dairy = False
        
        # get current allergy selections
        allergies = [{"dairy":False}, {"peanut":False}, {"gluten":False}, {"egg":False}, {"seafood":False}, {"grains":False}, {"shellfish":False}, {"sesame":False}, {"treenut":False}, {"soy":False}, {"wheat":False}, {"corn":False}]
        counter = 0
        # loop over each allergy item and convert list of dictionary to true if user selected allergy
        for item in allergies:
            print(counter)
            # get user selection from check box form
            if request.form.get(list(item.keys())[0]) == "":
                allergies[counter][list(item.keys())[0]] = True
            counter += 1

            # bug that goes out of range
            if counter == 12:
                break
        # get current diet selection from user input
        diet = request.form.get("diet")
        if request.form.getlist("clear") != None and request.form.getlist("clear") != []:
            diet = None

        try:
                # Connect to heroku hosted database \ any db in .env config
                connection = connectdb()

                # check if current user is in allergie table - if not then insert into db - if they are then update db
                # Create a cursor to perform database operations
                cursor = connection.cursor()
                # get usernames from db
                cursor.execute("""SELECT username FROM profile;""")
                usernames = cursor.fetchall()
                print(usernames)

                if (session["name"],) in usernames:
                    # Update allergies 
                    cursor.execute("""UPDATE profile SET diet = %s, dairy = %s, peanut = %s, gluten = %s, egg = %s, seafood = %s, grains = %s, shellfish = %s, sesame = %s, soy = %s, wheat = %s, corn = %s, tree_nut = %s WHERE username = %s;""", (diet, allergies[0]["dairy"], allergies[1]["peanut"], allergies[2]["gluten"], allergies[3]["egg"], allergies[4]["seafood"], allergies[5]["grains"], allergies[6]["shellfish"], allergies[7]["sesame"], allergies[9]["soy"], allergies[10]["wheat"], allergies[11]["corn"], allergies[8]["treenut"], session["name"]))
                    connection.commit()
                
                else:
                    # Insert allergies 
                    print(session["name"])
                    cursor.execute("""INSERT INTO profile (username, diet, dairy, peanut, gluten, egg, seafood, grains, shellfish, sesame, soy, wheat, corn, tree_nut) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""", (session["name"], diet, allergies[0]["dairy"], allergies[1]["peanut"], allergies[2]["gluten"], allergies[3]["egg"], allergies[4]["seafood"], allergies[5]["grains"], allergies[6]["shellfish"], allergies[7]["sesame"], allergies[9]["soy"], allergies[10]["wheat"], allergies[11]["corn"], allergies[8]["treenut"],))
                    connection.commit()
                
        except (Exception, Error) as error:
                print("Error while connecting to PostgreSQL", error)
                return render_template("profilesettingsdatabaseerror.html", user=session["name"])

        finally:
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")



        dairy = request.form.get("Dairy")
        #print(request.form.getlist())
        if dairy == "":
            print("test123")
        #print(type(checked))
        print("test")

        #return render_template("profilesettings.html", user=session["name"])

    # For Get request:
    print()

    # check if user already has allergies selected - if so then render template profilesettingsfilled
    #return render_template("profilesettingsfilled.html")
    try:
                # Connect to heroku hosted database \ any postgresql db in .env config
                connection = connectdb()

                # check if current user is in allergie table - if they are then update db - if not then return default profilesettings.html
                # Create a cursor to perform database operations
                cursor = connection.cursor()
                # get usernames from db
                cursor.execute("""SELECT username FROM profile;""")
                usernames = cursor.fetchall()
                print(usernames)
                
                if (session["name"],) in usernames:
                    print("i'm in the db")
                    # get current allergies for user to fill in check boxs for html page
                    cursor.execute("""SELECT * FROM profile WHERE username = %s;""", (session["name"],))
                    allergies = cursor.fetchall()
                    #allergies = list(cursor.fetchall()[0])
                
                    
                    # get only allergies from list of alergies db table and add true or false for each allergy in dictionary
                    # previous code for jinja html forloop 
                    # allergiesdict = [{"allergy":"Dairy","checked":False}, {"allergy":"Peanut","checked":False}, {"allergy":"Gluten","checked":False}, {"allergy":"Egg","checked":False}, {"allergy":"Seafood","checked":False}, {"allergy":"Grains","checked":False}, {"allergy":"Shellfish","checked":False}, {"allergy":"Sesame","checked":False}, {"allergy":"Soy","checked":False}, {"allergy":"Wheat","checked":False}, {"allergy":"Corn","checked":False}, {"allergy":"Tree Nut","checked":False}]
                    # allergieslist = []
                    print("291")
                    print(allergies)
                    # mod db list for only checkbox items
                    #allergies.pop(0)
                    #allergies.pop()
                    #allergies = tuple(allergies)
                    
                    print(allergies)
                    print(type(allergies[0][0]))
                    print(type(allergies[0][1]))
                    print(type(allergies[0][2]))
                    print(type(allergies[0][3]))
                    allergiesdict = [{"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}]
                    diet = None
                    counter = 0
                    for item in allergies[0]:
                        print(item)
                        print(type(item))
                        if type(item) == int:
                            continue
                        # get only allergies from list of alergies db table
                        if item == "true":
                            #allergieslist.append(item)
                            # add true or false for each allergy in dictionary                          
                            allergiesdict[counter]["checked"] = True
                            counter += 1
                        if item == "false":
                            #allergieslist.append(item)
                            # add true or false for each allergy in dictionary                          
                            allergiesdict[counter]["checked"] = False
                            counter += 1
                        # get diet if user has one selected currently
                        if item != None and counter == 0:
                            diet = item
                            
                            
                        
                    print(diet)        
                    print(allergiesdict)
                    if request.method == "POST":
                        
                        return render_template("profilesettingsfilledupsaved.html", allergies=allergiesdict, user=session["name"], diet=diet)

                    return render_template("profilesettingsfilledup.html", allergies=allergiesdict, user=session["name"], diet=diet)

                 
                
                
    except (Exception, Error) as error:
            print("Error while connecting to PostgreSQL", error)
            return render_template("profilesettingsdatabaseerror2.html", user=session["name"])

    finally:
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
    # render default profilesettings without any selected
    return render_template("profilesettings.html", user=session["name"])   


@app.route("/getrecipe", methods=["POST", "GET"])
@login_required
def getrecipe():
    # get random recipe with allergies accounted for
    # first get food query type from user
    # insert food query type and intolerances into url api call 
    # take api response and get all food IDs
    
    if request.method == "POST":
        # if user selects favorites button from api error page
        if request.form.getlist("favorites") != None and request.form.getlist("favorites") != []:
            return redirect("/favorites")
        # if user selects save to favorites button insert recipe id into favorites db table and return user to getrecipe.html
        if request.form.getlist("save") != None and request.form.getlist("save") != []:
            print("save")
            print(session["recipe"])
            #print(request.session)

            # connect to db and insert current recipe information 
            try:
                # Connect to heroku hosted database \ any db in .env config
                connection = connectdb()
                # Create a cursor to perform database operations
                cursor = connection.cursor()
                # insert new favorite recipe into favorites table
                cursor.execute("""INSERT INTO favorites (recipeid, image, title, link, date, username) VALUES (%s, %s, %s, %s, %s, %s);""", (session["recipe"], session["image"], session["title"], session["link"], session["date"], session["name"]))
                connection.commit()
                
            except (Exception, Error) as error:
                    print("Error while connecting to PostgreSQL", error)
                    return render_template("profilesettingsdatabaseerror2.html", user=session["name"])

            finally:
                if (connection):
                    cursor.close()
                    connection.close()
                    print("PostgreSQL connection is closed")
                    return render_template("getrecipesaved.html")

        # get current users intolerances from db
        try:
            # Connect to heroku hosted database \ any db in .env config
            connection = psycopg2.connect(user=os.environ.get('dbuser'),
                            password=os.environ.get('dbpassword'),
                            host=os.environ.get('dbhost'),
                            port=os.environ.get('dbport'),
                            database=os.environ.get('dbdatabase'))

            # check if current user is in profile table - if they are then update db - if not then return default profilesettings.html
            # Create a cursor to perform database operations
            cursor = connection.cursor()
            # get usernames from db
            cursor.execute("""SELECT username FROM profile;""")
            usernames = cursor.fetchall()
            print(usernames)
            
            if (session["name"],) in usernames:
                print("i'm in the db")
                # get current allergies for user to fill in check boxs for html page
                cursor.execute("""SELECT * FROM profile WHERE username = %s;""", (session["name"],))
                profile = cursor.fetchall()
                
                # get only allergies from list of alergies db table and add true or false for each allergy in dictionary
                # previous code for jinja html forloop 
                # allergiesdict = [{"allergy":"Dairy","checked":False}, {"allergy":"Peanut","checked":False}, {"allergy":"Gluten","checked":False}, {"allergy":"Egg","checked":False}, {"allergy":"Seafood","checked":False}, {"allergy":"Grains","checked":False}, {"allergy":"Shellfish","checked":False}, {"allergy":"Sesame","checked":False}, {"allergy":"Soy","checked":False}, {"allergy":"Wheat","checked":False}, {"allergy":"Corn","checked":False}, {"allergy":"Tree Nut","checked":False}]
                #allergiesdict = [{"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}, {"checked":False}]
                newstring = ""
                dictionary = {3:"dairy", 4:"peanut", 5:"gluten", 6:"egg", 7:"seafood", 8:"grains", 9:"shellfish", 10:"sesame", 11:"tree_nut", 12:"soy", 13:"wheat", 14:"corn"}
                diet = None
                # set counter to 0 so we skip diet column from db table
                counter = 0
                for item in profile[0]:
                    # get diet if user has one selected currently
                    if item != None and counter == 2:
                        diet = item
                    # get only allergies / intolerances from list of profile db table 
                    if item == "true":
                        # instert intolorances into new string if allergy is marked true in db table
                        if newstring == "":
                            newstring = dictionary[counter]
                        else:
                            newstring = f"{newstring}, {dictionary[counter]}"
                    counter += 1
                print(profile)    
                print(diet)
                if diet:
                    print("true")
                print(newstring)
                #return render_template("profilesettingsfilledup.html", allergies=allergiesdict, user=session["name"])
                # if user is not in profile db table - set to default
            else:
                newstring = ""
                diet = None
            
            # try using first api else try second api key
            try:
                return api_request(os.environ.get('api_key1'), newstring, diet)
            except:
                # try using second api else try second third key
                try:
                    return api_request(os.environ.get('api_key2'), newstring, diet)
                except:
                    # try using third api else return out of api keys page
                    try:
                        return api_request(os.environ.get('api_key3'), newstring, diet)
                    except:
                        return render_template("noapicallsleftonapikey.html")
                    
                    
                    
        except (Exception, Error) as error:
                print("Error while connecting to PostgreSQL", error)
                return render_template("profilesettingsdatabaseerror2.html", user=session["name"])

        finally:
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")


       
    # Get request    
    
    return render_template("getrecipe.html")


@app.route("/favorites", methods=["GET"])
@login_required
def favorites():
    # for get request, connect to db and get list of favorites for current user 
    try:
                # Connect to heroku hosted database \ any db in .env config
                connection = connectdb()
                
                # check if current user is in favorites table - if they are then get list of favorites - if not then return favoritesnone.html
                # Create a cursor to perform database operations
                cursor = connection.cursor()
                # get usernames from db
                cursor.execute("""SELECT username FROM favorites;""")
                usernames = cursor.fetchall()
                print(usernames)
                if (session["name"],) in usernames:
                    # get list of favorites for current user 
                    cursor.execute("""SELECT * FROM favorites WHERE username = %s;""", (session["name"],))
                    favorites = cursor.fetchall()
                    print(favorites)
                    print(favorites[0][0])
                else:
                    return render_template("favoritesnone.html", user=session["name"])
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return render_template("favoritesdatabaseerror.html", user=session["name"])

    finally:
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
    
    print(favorites)
    return render_template("favorites.html", favorites=favorites, user=session["name"])



def connectdb():
    # Connect to heroku hosted database \ any db in .env config
    connection = psycopg2.connect(user=os.environ.get('dbuser'),
                        password=os.environ.get('dbpassword'),
                        host=os.environ.get('dbhost'),
                        port=os.environ.get('dbport'),
                        database=os.environ.get('dbdatabase'))
    return connection


def api_request(apikey, newstring, diet):
    print(apikey)
    # get cuisine input from user
    cuisine = request.form.get("cuisine")
    cuisinelist = ["","African", "American","British","Cajun","Caribbean","Chinese","Eastern European","European","French","German","Greek","Indian","Irish","Italian","Japanese","Jewish","Korean","Latin American","Mediterranean","Mexican","Middle Eastern","NordicSouthern","Spanish","Thai","Vietnamese"]
    # if cuisine entered from user is not supported render invalid template
    if string.capwords(cuisine) not in cuisinelist:
        return render_template("getrecipecuisinenotvalid.html")
    
    print(newstring)
    print(diet)
    # if user selects new main dish button change api url
    if request.form.getlist("main") != None and request.form.getlist("main") != []:
        url1 =  "https://api.spoonacular.com/recipes/complexSearch?apiKey=%s&query=%s&number=100&intolerances=%s&type=main course&diet=%s" % (apikey, cuisine, newstring, diet)
    # if user selects new main dish button change api url
    elif request.form.getlist("desert") != None and request.form.getlist("desert") != []:
        url1 =  "https://api.spoonacular.com/recipes/complexSearch?apiKey=%s&query=%s&number=100&intolerances=%s&type=dessert&diet=%s" % (apikey, cuisine, newstring, diet)
    # if user selects new main dish button change api url
    elif request.form.getlist("suprise") != None and request.form.getlist("suprise") != []:
        url1 =  "https://api.spoonacular.com/recipes/complexSearch?apiKey=%s&query=%s&number=100&intolerances=%s&diet=%s" % (apikey, cuisine, newstring, diet)
    # if none return getrecipe.html
    else:
        return render_template("getrecipesaved.html")

    print(request.form.getlist("main"))
    print(request.form.getlist("desert"))
    print(request.form.getlist("suprise"))
    print(url1)
    

    
    print(type(cuisine))
    
    # get list of cuisine excluding recipes that contain users intolerances - old
    #url1 = "https://api.spoonacular.com/recipes/complexSearch?apiKey=%s&query=%s&number=100&intolerances=%s" % (apikey, cuisine, newstring) #note: add in query variable in place of american
    print(url1)
    response = requests.get(url1)
    # get list of dictionaries from api using json function
    recipes = response.json()
    # get only results dictionary 
    recipes = recipes["results"]
    # get random recipe from list of recipes
    # if results is empty return no recipes found within profile settings
    if recipes == []:
        return render_template("getrecipenotfound.html")
    randomrecipe = random.choice(recipes)
    # get recipe id from random recipe
    newrecipeid = randomrecipe["id"]
    print(newrecipeid)
    print("test2")
    # get image from random recipe
    newrecipeimg = randomrecipe["image"]
    print(newrecipeimg)
    # get title of recipe
    newrecipetitle = randomrecipe["title"]
    print(newrecipetitle)

    # get recipe information for id selected https://api.spoonacular.com/recipes/632342/information?apiKey=
    url2 = "https://api.spoonacular.com/recipes/%s/information?apiKey=%s" % (newrecipeid, apikey)
    print(url2)
    response2 = requests.get(url2)
    source = (response2.json())["sourceUrl"]
    print(source)
    #img = (response2.json())[""]
    # get recipe nutritional information 
    url3 = "https://api.spoonacular.com/recipes/%s//nutritionWidget.json?apiKey=%s" % (newrecipeid, apikey)
    response3 = requests.get(url3)
    nutrition = response3.json()
    nutritionlist = [nutrition["calories"], nutrition["carbs"], nutrition["fat"], nutrition["protein"]]
    print(nutritionlist)

    # get recipe ingredients for id selected  https://api.spoonacular.com/recipes/1003464/ingredientWidget.json?
    url4 = "https://api.spoonacular.com/recipes/%s/ingredientWidget.json?apiKey=%s" % (newrecipeid, apikey)
    response4 = requests.get(url4)
    ingredients = response4.json()
    # get ingredients dictionary from api call
    ingredients = ingredients["ingredients"]
    ingredientslist = []
    # get all names of ingredients from list of dictionarys
    for item in ingredients:
        # get current ingredient, convert to first letter capital then insert into list of ingredients
        ingredientslist.append((item["name"]).capitalize())
        
    print(ingredientslist)
    print(url4)
    # set current session recipe 
    session["recipe"] = newrecipeid
    # set current session recipe image
    session["image"] = newrecipeimg
    # set current session recipe title
    session["title"] = newrecipetitle
    # set current session recipe link
    session["link"] = source
    # set current date when saved
    todays_date = date.today()
    # re-order string for day month year
    todays_date = str(todays_date.day) + '-' + str(todays_date.month) + '-' + str(todays_date.year)
    session["date"] = (todays_date)

    return render_template("getrecipefilled.html", image=newrecipeimg, title=newrecipetitle, link=source, nutrition=nutritionlist, cuisine=cuisine, ingredients=ingredientslist)
