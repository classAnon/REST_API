import os
import hashlib
from bson.json_util import dumps
import datetime
from flask_cors import cross_origin
from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, make_response, request, jsonify
from bson.objectid import ObjectId
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity



load_dotenv()

app = Flask(__name__)


jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=8)


client = MongoClient(os.getenv("CONNECTION_STRING"))
db = client[os.getenv("DB_NAME")]
templates_collection = db["templates"]


@app.route('/register/', methods=["POST"])
@cross_origin()
def register():

	new_user = request.get_json()
	user_pwd = hashlib.sha256(new_user['password'].encode("utf-8")).hexdigest()
	new_user["password"] =  user_pwd

	current_collection = db.users
	doc = current_collection.find_one({"email": new_user["email"]})
	if not doc:
		current_collection.insert_one(new_user)
		return jsonify({'msg': 'User created successfully'}), 201
	else:
		return jsonify({'msg': 'Username already exists'}), 409


@app.route('/login/', methods=["POST"])
@cross_origin()
def login():

	login_info = request.get_json()
	current_collection = db.users
	user_from_db = current_collection.find_one({'email': login_info['email']})

	if user_from_db:
		encrpted_password = hashlib.sha256(login_info['password'].encode("utf-8")).hexdigest()
		if encrpted_password == user_from_db['password']:
			access_token = create_access_token(identity=str(user_from_db['_id']))
			return jsonify(access_token=access_token), 200
	return jsonify({'msg': 'The username or password is incorrect'}), 401

@app.route('/template/', methods=["POST"])
@jwt_required()
def create_template():

	template = request.get_json()

	template_data = {
		"template_name": template["template_name"],
		"subject": template["subject"],
		"body": template["body"],
		"user_id": get_jwt_identity()	
	}

	temp = templates_collection.find_one({"template_name": template["template_name"]})
	if not temp:
		templates_collection.insert_one(template_data)
		return jsonify({'msg': 'Template created successfully'}), 201
	else:
		return jsonify({'msg': 'Template already in collection'}), 409

	
@app.route('/template/', methods=["GET"])
@jwt_required()
def retrieve_all_templates():

	templates = list(templates_collection.find({"user_id":get_jwt_identity()}))

	holder = list()

	for i in templates:
		holder.append(i)
		i['_id'] = str(i['_id'])

	json_data = dumps(str(holder))
	return make_response(json_data), 200


@app.route('/template/<id>', methods=["GET"])
@jwt_required()
def retrieve_one_template(id):

	get_jwt_identity()

	data = dumps(templates_collection.find_one({"_id": ObjectId(id)}))
	if data:
		return make_response(data), 200
	else:
		return jsonify({'msg': 'No such template in current collection'}), 500

		

@app.route('/template/<id>', methods=["PUT"])
@jwt_required()
def update_data(id):

	get_jwt_identity()

	req = request.get_json()

	template = templates_collection.find_one({"user_id":get_jwt_identity()})
	if template:
		templates_collection.update_one({"_id": template['_id']}, {'$set': {'template_name': req.get('template_name'), 'subject': req.get('subject'), 'body': req.get('body')}})
		return jsonify({'msg': 'template successfully updated.'}), 200
	else:
		return jsonify({'msg': 'nothing to update'}), 200


@app.route('/template/<id>', methods=["DELETE"])
@jwt_required()
def delete(id):

	get_jwt_identity()

	template = templates_collection.find_one({"user_id":get_jwt_identity()})
	if template:
		templates_collection.delete_one(template)
		return jsonify({'msg': 'template successfully removed'}), 200
	else:
		return jsonify({'msg': 'template not found in collection'}), 500
	

if __name__ == '__main__':
	app.run(Debug=True)
