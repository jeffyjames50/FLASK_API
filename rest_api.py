import pymongo
import os
from dotenv import load_dotenv
from flask import Flask
from flask import request, jsonify
from flask_cors import CORS

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
print(mongo_uri)
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable is not set!")

myclient = pymongo.MongoClient(mongo_uri)
mydb = myclient['mydatabase']
myclu = mydb['books']

app= Flask(__name__)
cors=CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

#Endpoint to insert one book
'''@app.route("/Push", methods=["Post","GET"])
def Push():
    content = request.get_json()
    myclu.insert_one(content)
    return("Push initiated")

#Endpoint to insert multiple book
@app.route("/PushMany", methods=["Post","GET"])
def PushMany():
    content = request.get_json()
    myclu.insert_many(content)
    return("Push initiated")'''

# Endpoint to insert a single book
@app.route("/Push", methods=["POST"])
def Push():
    content = request.get_json()
    isbn = content.get("isbn")
    
    if not isbn:
        return jsonify({"error": "ISBN is required"}), 400

    available_copies = content.pop("available_copies", 0)  # Remove 'available_copies' from the update fields
    
    # Update if book with the same ISBN exists, otherwise insert a new book
    result = myclu.update_one(
        {"isbn": isbn},  # Search by ISBN
        {
            "$set": content,  # Update other fields
            "$inc": {"available_copies": available_copies}  # Increment available copies
        },
        upsert=True  # Insert if not found
    )
    
    return jsonify({"message": "Push initiated for single book"})

# Endpoint to insert or update multiple books
@app.route("/PushMany", methods=["POST"])
def PushMany():
    content = request.get_json()

    if not isinstance(content, list):
        return jsonify({"error": "Input must be a list of books"}), 400

    for book in content:
        isbn = book.get("isbn")
        if not isbn:
            continue  # Skip books without ISBN
        
        available_copies = book.pop("available_copies", 0)  # Remove 'available_copies' from the update fields
        
        # Update if book with the same ISBN exists, otherwise insert a new book
        myclu.update_one(
            {"isbn": isbn},  # Search by ISBN
            {
                "$set": book,  # Update other fields
                "$inc": {"available_copies": available_copies}  # Increment available copies
            },
            upsert=True  # Insert if not found
        )
    
    return jsonify({"message": "Push initiated for multiple books"})
    
#Endpoint to update the number of available copies based on the isbn 
@app.route("/Update", methods=["Post","GET"])
def Update():
    content = request.get_json()
    myval= {"$set":{"available_copies":content['available_copies']}}
    myclu.update_one({"isbn":content["isbn"]},myval)
    return("Update initiated")

#Endpoint to delete an entry based on the isbn
@app.route("/Delete", methods=["Post","GET"])
def Delete():
    content = request.get_json()
    myclu.delete_one({"isbn":content["isbn"]})
    return("Delete initiated")

#Endpoint to fetch a book details based on isbn
@app.route("/SearchBooks", methods=["GET"])
def SearchBooks():
    # Get query parameters
    title = request.args.get("title")
    author = request.args.get("author")
    genre = request.args.get("genre")
    isbn = request.args.get("isbn")

    # Build a dynamic query
    query = {}
    if title:
        query["title"] = {"$regex": title, "$options": "i"}  # Case-insensitive search
    if author:
        query["author"] = {"$regex": author, "$options": "i"}  # Case-insensitive search
    if genre:
        query["genre"] = {"$regex": genre, "$options": "i"}  # Case-insensitive search
    if isbn:
        query["isbn"] = {"$regex": isbn, "$options": "i"}

    # Search in the database
    results = list(myclu.find(query, {"_id": 0}))  # Exclude '_id' from results

    # Return results
    if results:
        return jsonify({"books": results}), 200
    else:
        return jsonify({"message": "No books found matching the criteria"}), 404

@app.route("/PullAll", methods=["GET"])
def PullAll():
    books = list(myclu.find({}, {"_id": 0}))  # Exclude the '_id' field for cleaner output

    # Check if the collection is empty
    if books:
        return jsonify({"books": books}), 200
    else:
        return jsonify({"message": "No books found"}), 404


if __name__ =="__main__":
    app.run()
