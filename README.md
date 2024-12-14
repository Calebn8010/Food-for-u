# Food-for-you
#### Discover new recipes to integrate into your home recipe book. Optimized for your health with filters for ceritian allergies and diets. Utilizing Spoontacular API every recipe provided will be compatible with your user profile settings. Desktop and Mobile friendly.
#### You can check it out here! "https://food-for-u.herokuapp.com/"

# Local setup instructions
### Make sure to clone the "run_local" branch and not the main branch.
### Best to run within a python virtual environment. Make sure to install these python libraries listed in the requirements.txt (pip install -r requirements.txt) once your venv is activated.
### Make sure you can start your local host flask server with "flask --app app run". Reference https://flask.palletsprojects.com/en/stable/quickstart/
####
### Setup local testing postgresql database with tables: users, profile, favorites. Table columns must match flask app, Psql create table commands below:
#### `CREATE TABLE users (`
####   `id SERIAL PRIMARY KEY,`
####    `username VARCHAR(50) UNIQUE NOT NULL,`
####    `passwordhash TEXT NOT NULL,`
####    `created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP AT TIME ZONE 'America/New_York'`
#### `);`

####
#### `CREATE TABLE profile (`
####     `id SERIAL PRIMARY KEY,`
####    `username VARCHAR(50) UNIQUE NOT NULL,`
####    `diet VARCHAR(50),`
####    `dairy VARCHAR(50),`
####    `peanut VARCHAR(50),`
####    `gluten VARCHAR(50),`
####    `egg VARCHAR(50),`
####    `seafood VARCHAR(50),`
####    `grains VARCHAR(50),`
####    `shellfish VARCHAR(50),`
####    `sesame VARCHAR(50),`
####    `soy VARCHAR(50),`
####    `wheat VARCHAR(50),`
####    `corn VARCHAR(50),`
####    `tree_nut VARCHAR(50),`
####    `created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP AT TIME ZONE 'America/New_York'`
#### `);`

####
#### `CREATE TABLE favorites (`
####    `id SERIAL PRIMARY KEY,`
####    `recipeid VARCHAR(50),`
####    `username VARCHAR(50) NOT NULL,`
####    `image TEXT,`
####    `title TEXT,`
####    `link TEXT,`
####    `date TEXT,`
####    `created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP AT TIME ZONE 'America/New_York'`
#### `);`

### Create .env file with config values required for db, server host and api key from spoonacular: 
#### dbuser=""
#### dbpassword=""
#### dbhost=""
#### dbport=""
#### dbdatabase=""
#### homepage=""
#### api_key1=""
#### (if local host - homepage should be similar to "http://127.0.0.1:5000"). References, dotenv: https://pypi.org/project/python-dotenv/, create spoonacular api key: https://spoonacular.com/food-api/console#Dashboard

