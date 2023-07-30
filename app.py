from flask import Flask, request
import os, json
from uuid import uuid4

app = Flask(__name__)

db = {}
db_filename = "db.json"

# checked whether db.json exists or not
if os.path.exists(db_filename):
    with open(db_filename, 'r') as f:
        db = json.load(f) # database elements loaded to db object
else:
    # create the initial db object
    db = {
        "users": [],
        "groups": []
    }

    with open(db_filename, 'w+') as f:
        json.dump(db, f, indent=4) # dump the data into the db.json file

print(db)

# write your apis here

@app.route('/signup', methods=['POST'])
def signup():
    request_body = request.json
    # print(request_body)
    # we have write the signup logic here
    
    # check whether users key exists or not
    if "users" in list(db.keys()):
        # checking for users with similar email id
        if check_duplicate_user(request_body) == False:
            user_id = str(uuid4())
            
            user_obj = {
                "user_id": user_id,
                "email": request_body["email"],
                "password": request_body["password"],
                "expense": {
                    "personal": [],
                    "group": []
                }
            }

            db["users"].append(user_obj)

            with open(db_filename, "r+") as f:
                json.dump(db, f, indent=4)

            return "Signup successful"
        else:
            return "Error: User with same email id already exists"
    else:
        return "Something went wrong"
    
def check_duplicate_user(request_body):
    for user in db["users"]:
        if request_body["email"] == user["email"]:
            return True
    return False

@app.route("/login", methods=["POST"])
def login():
    request_body = request.json

    user, flag = check_user_credential(request_body)
    user_obj = {}
    if flag == True:
        user_obj = {
            "user_id": user["user_id"],
            "email": user["email"]
        }

    return user_obj

def check_user_credential(request_body):
    for user in db["users"]:
        if request_body["email"] == user["email"] and request_body["password"] == user["password"]:
            return user, True
    
    return None, False

@app.route("/group/create", methods=["POST"])
def create_group():
    request_body = request.json
    """
    {
        "user_id": "",
        "group_name": "",
        "members" :["abc@xyz.com", "tyg@xyz.com"]
    }
    """

    if "groups" in list(db.keys()):
        group_id = str(uuid4())
        group_name = request_body["group_name"]
        members = []

        for member in request_body["members"]:
            if check_existing_user(member):
                members.append(member)
            else:
                # send mail or sms invite to user
                continue


        group_obj = {
            "group_admin": request_body["user_id"],
            "group_id": group_id,
            "group_name": group_name,
            "members": members,
            "expense": []
        }
        db["groups"].append(group_obj)
        with open(db_filename, 'r+') as f:
            json.dump(db, f, indent=4)

        return group_obj
    else:
        return "Something went wrong"

def check_existing_user(email):
    for user in db["users"]:
        if user["email"] == email:
            return True
    return False

@app.route("/group/add-member", methods=["POST"])
def add_member():
    request_body = request.json
    """
    {
    "user_id": "give the user id you have logged in from",
    "group_id": "the group you want to add member to",
    "members": [] 
    }
    """

    #check if the group id exists or not
    target_group, flag = check_existing_groups(request_body)
    if flag:
        for member in request_body["members"]:
            if check_existing_user(member) and check_existing_member(target_group, member) == False:
                target_group["members"].append(member)
            else:
                continue
        with open(db_filename, 'r+') as f:
            json.dump(db, f, indent=4)
        return "Member added successfully"
    else:
        return "Group does not exist"

def check_existing_groups(request_body):
    for group in db["groups"]:
        if group["group_id"] == request_body["group_id"]:
            return group, True
    return None, False

def check_existing_member(target_group, email):
    print(target_group)
    for member in target_group["members"]:
        if member == email:
            return True
    return False

@app.route('/add-expense', methods=['POST'])
def add_expense():
    """
    {
        "user_id": "",
        "title": "",
        "amount": ""
    }
    """
    request_body = request.json

    user, flag = get_user_from_id(request_body["user_id"])

    if flag:
        user_expense = user["expense"]["personal"]

        expense_obj = {
            "id": str(uuid4()),
            "title": request_body["title"],
            "amount": request_body["amount"]
        }

        user_expense.append(expense_obj)

        with open(db_filename, "r+") as f:
            json.dump(db, f, indent=4)
        return "Expense Added Successfully"
    else:
        return "user not found"

def get_user_from_id(user_id):
    for user in db["users"]:
        if user["user_id"] == user_id:
            return user, True
    return None, False


@app.route("/group/get-all-members", methods=["GET"])
def group_get_all_members():
    group_id = request.args.get("group_id")

    group, flag = get_group_from_id(group_id)

    members = []
    if flag:
        for member in group["members"]:
            members.append({
                "email": member,
                "user_id": get_id_from_email(member),
            })
        return {"members": members}
    else:
        return "Group does not exist"

def get_id_from_email(email):
    target_user_id = None
    for user in db["users"]:
        if user["email"] == email:
            target_user_id = user["user_id"]
    return target_user_id

@app.route('/group/add-expense', methods=['POST'])
def add_group_expense():
    """
    {
        "user_id",
        "group_id",
        "title",
        "amount",
        "split" : [
            {"member_id": "split_percentage}
        ]

    }
    """
    request_body = request.json
    print(request_body)

    target_group, flag = get_group_from_id(request_body['group_id'])

    if flag:
        expense_obj = {
            "title": request_body['title'],
            "amount": request_body['amount']
        }
        # member_count = len(target_group["members"])
        # i = 0
        for split in request_body['split']:
            print(split)
            target_user_id = list(split.keys())[0]
            print(target_user_id)
            expense_obj[target_user_id] = get_split_amount(request_body['amount'], split[target_user_id])
            # i = i+1
            # if i>member_count:
            #     break
        target_group["expense"].append(expense_obj)

        with open(db_filename, "r+") as f:
            json.dump(db, f, indent=4)

        return "group expense added successfully"
    else:
        return "group not found"

def get_split_amount(total_amount, split_perc):
    return float(total_amount)*float(split_perc)

def get_group_from_id(group_id):
    for group in db["groups"]:
        if group["group_id"] == group_id:
            return group, True
    return None, False

if __name__ == '__main__':
    print(app.url_map)
    app.run(host='0.0.0.0', port="5000", debug=True)