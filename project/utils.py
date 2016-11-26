import os
# import MySQLdb
from sqlalchemy import create_engine


# These environment variables are configured in app.yaml.
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')
CLOUDSQL_DATABASE = os.environ.get('CLOUDSQL_DATABASE')

# def connect_to_cloudsql():
#     # When deployed to App Engine, the `SERVER_SOFTWARE` environment variable
#     # will be set to 'Google App Engine/version'.
#     if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
#         # Connect using the unix socket located at
#         # /cloudsql/cloudsql-connection-name.
#         cloudsql_unix_socket = os.path.join(
#             '/cloudsql', CLOUDSQL_CONNECTION_NAME)
# 
#         db = MySQLdb.connect(
#             unix_socket=cloudsql_unix_socket,
#             user=CLOUDSQL_USER,
#             passwd=CLOUDSQL_PASSWORD)
# 
#     # If the unix socket is unavailable, then try to connect using TCP. This
#     # will work if you're running a local MySQL server or using the Cloud SQL
#     # proxy, for example:
#     #
#     #   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
#     #
#     else:
#         db = MySQLdb.connect(
#             host='127.0.0.1', user=CLOUDSQL_USER, passwd=CLOUDSQL_PASSWORD)
# 
#     return db

def create_cloudsql_engine():
    # When deployed to App Engine, the `SERVER_SOFTWARE` environment variable
    # will be set to 'Google App Engine/version'.
    credentials = {
        'user': CLOUDSQL_USER,
        'password': CLOUDSQL_PASSWORD,
        'connection_name': CLOUDSQL_CONNECTION_NAME,
        'database': CLOUDSQL_DATABASE,
    }
    if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
        connection_string = 'mysql+mysqldb://{user}:{password}@{database}' \
            '?unix_socket=/cloudsql/{connection_name}'.format(**credentials)
    # If the unix socket is unavailable, then try to connect using TCP. This
    # will work if you're running a local MySQL server or using the Cloud SQL
    # proxy, for example:
    #
    #   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
    #
    else:
        connection_string = 'mysql+mysqldb://{user}:{password}@127.0.0.1:3306/{database}' \
            .format(**credentials)

    return create_engine(connection_string)

