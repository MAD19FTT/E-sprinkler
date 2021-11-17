# 
# import mysql.connector

# db = mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="",
#         database="sprinkler",
#         port=3306
#     )

# To test connection on MySQL databases
# import libraries
import mysql.connector

db = mysql.connector.connect(host="128.199.176.62",
                             user="sam",
                             password="password",
                             port="3306",
                             database="sprinkler")