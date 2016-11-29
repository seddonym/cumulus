=======
Cumulus
=======

Cumulus is a tornado web app designed to run on Google App Engine.

Local development
-----------------

Download a credentials file from Google Cloud at https://console.developers.google.com/projectselector/apis/credentials.

Start a proxy to the Google Cloud SQL server::

    cloud_sql_proxy -instances=<google-cloud-connection-name>=tcp:3306 -credential_file=credentials.json

Create a Google Cloud SQL database using the proxy.
 
Create a virtual environment and install the requirements::

    $ mkvirtualenv cumulus
    $ pip install -r requirements.pip


Export the environment variables into your shell::

    export CLOUDSQL_CONNECTION_NAME=<google-cloud-connection-string>
    export CLOUDSQL_USER=<username>
    export CLOUDSQL_PASSWORD=<password>
    export CLOUDSQL_DATABASE=<local_database_name>

Create the initial database schema::

    python project/sqlalchemy_insert.py

To run the development server, create an ``app.yaml`` file in the following format::

    runtime: python27
    api_version: 1
    threadsafe: yes
    
    handlers:
    - url: /static/
      static_dir: static
    
    - url: /.*
      script: project.main.application
      
    libraries:
    - name: MySQLdb
      version: "latest"
    - name: numpy
      version: "1.6.1"
    - name: pycrypto
      version: "2.6"
    
    env_variables:
        CLOUDSQL_CONNECTION_NAME: cumulus-150709:europe-west1:cumulus-mysql
        CLOUDSQL_USER: <username>
        CLOUDSQL_PASSWORD: <password>
        CLOUDSQL_DATABASE: <local_database_name>
        WORD_HASH_SALT: <random string - keep secret>
        WORD_PRIVATE_KEY: <RSA private key - keep secret>

Run the development server::

    cd path/to/cumulus
    dev_appserver.py .

The server should be accessible at http://localhost:8080/.

Deployment
----------

Install requirements into lib::

    pip install -t lib -r requirements.pip

To push to Google App Engine, edit the `app.yaml` to point to the correct
database, then::

    gcloud app deploy app.yaml
