Username = "allen"
Password = "walker"

class User:
    def __init__(var,id,username,password):
        var.id = id
        var.username = username
        var.password = password

userlist = []
userlist.append(User(id = 1, username = "mana", password = "walker"))
userlist.append(User(id = 2, username = "allen", password = "walker"))
userlist.append(User(id = 3, username = "kanda", password = "yu"))

for x in userlist:
    if x.username == Username:
        if x.password == Password:
            print("success")
        else:
            print("wrong password")
    else:
        print("nonexistent username")

