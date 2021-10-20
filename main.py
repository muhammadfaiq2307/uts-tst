#Muhammad Faiq Dhiya Ul Haq
#18219013
#Simple CRUD API using FastAPI (python3)

import json
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt

with open("users.json", "r") as read_file:
    data_user = json.load(read_file)

with open("menu.json", "r") as read_file:
    data = json.load(read_file)

load_dotenv()
app = FastAPI()

skema_oauth2 = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.environ.get("secret_key")
ALGORITHM = os.environ.get("algorithm")

# Class of Token
class Token(BaseModel):
    access_token: str
    token_type: str

# Context to hashing, using bcrypt
context_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Verifying between plain password and hashed password (plain password after hashed)
def verifying_password(plain_password, hashed_password):
    return context_pwd.verify(plain_password, hashed_password)

# Find a user from users.json file
def get_user(username:str):
    for user in data_user:
        if username == user["username"]:
            return user
    return "No user has been found"

# Simple authentication function by verifying username and password
def authenticate_user(username:str, password:str):
    user = get_user(username)
    if not user:
        return False
    if not verifying_password(password, user["password"]):
        return False
    return user

# print(authenticate_user("asdf", "asdf"))

# Create a token
def create_token(user):
    encoded_jwt = jwt.encode(user, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# print(create_token(authenticate_user("asdf", "asdf")))

# Function to authorize user
async def get_current_user(token: str = Depends(skema_oauth2)):
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate user credentials",
        headers = {"WWW-Authenticate" : "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        username:str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

# Get the current active user
async def get_current_active_user(current_user = Depends(get_current_user)):
    if current_user["disabled"]:
        raise HTTPException(
            status_code = 400,
            detail = "Inactive User"
        )
    return current_user

# Token authentication route
@app.post("/token")
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_to_auth = authenticate_user(form_data.username, form_data.password)
    if not user_to_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate" : "Bearer"}
        )
    access_token = create_token(user={"sub" : user_to_auth["username"]})
    return {
        "access_token" : access_token,
        "token_type" : "bearer"
    }

# Root path landing
@app.get("/")
def root():
    return {
        "status" : "Server is up and running on port 8000",
        "Message" : "Please proceed to https://api-authentication-18219113.herokuapp.com/docs for API details"
        }

# READ data

# Read all data
@app.get("/menu")
async def read_all_menu(current_user = Depends(get_current_active_user)):
    if(len(data["menu"]) > 0):
        return data["menu"]
    raise HTTPException(status_code=404, detail=f"Item not found")

# Read a specific data, acquired based on item_id
@app.get("/menu/{item_id}")
async def read_menu(item_id: int, current_user = Depends(get_current_active_user)):
    for menu_item in data["menu"]:
        if menu_item["id"] == item_id:
            return menu_item
    raise HTTPException(status_code=404, detail=f"Item not found")


# CREATE a new data and add it on to menu.json
@app.post("/menu")
async def add_new_menu(name : str, current_user = Depends(get_current_active_user)):
    id = 1
    if(len(data["menu"]) > 0):
        id = data["menu"][len(data["menu"]) - 1]["id"] + 1
    new_menu = {
        "id" : id,
        "name" : name
    }
    data["menu"].append(dict(new_menu))
    read_file.close()

    with open("menu.json", "w") as writen_file:
        json.dump(data, writen_file, indent=4)
    writen_file.close()

    return new_menu

    raise HTTPException(
        status_code=500, detail=f"Internal Server Error"
    )

# UPDATE a certain menu item's name. A menu item will be searched by its id
@app.put("/menu/{item_id}")
async def update_menu(item_id : int, name : str, current_user = Depends(get_current_active_user)):
    for menu_item in data["menu"]:
        if(menu_item["id"] == item_id):
            menu_item["name"] = name
            read_file.close()
            with open("menu.json", "w") as writen_file:
                json.dump(data, writen_file, indent=4)
            writen_file.close()
            return {"status" : "Item successfully updated"}
    raise HTTPException(
        status_code=404, detail="Item not found"
    )

# DELETE menu

# Delete all menu
@app.delete("/menu")
async def delete_all_menu(current_user = Depends(get_current_active_user)):
    data["menu"].clear()
    read_file.close()
    with open("menu.json", "w") as writen_file:
        json.dump(data, writen_file, indent=4)
    writen_file.close()
    return {"status" : "All menus successfully deleted"}
    raise HTTPException(
        status_code=404, detail="Item not found"
    )

# Delete a specific menu. The specific menu item will be specified by id/item_id
@app.delete("/menu/{item_id}")
async def delete_menu(item_id : int, current_user = Depends(get_current_active_user)):
    for menu_item in data["menu"]:
        if(menu_item["id"] == item_id):
            data["menu"].remove(menu_item)
            read_file.close()
            with open("menu.json", "w") as writen_file:
                json.dump(data, writen_file, indent=4)
            writen_file.close()
            return {"status" : "Item successfully deleted"}
    raise HTTPException(
        status_code=404, detail="Item not found"
    )
