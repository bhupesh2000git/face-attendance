import cv2
import face_recognition
import os
import numpy as np
from datetime import datetime
import csv
from flask import Flask, render_template, request, jsonify
import base64

app = Flask(__name__)

# Directories and files
KNOWN_FACES_DIR = "known_faces"
ATTENDANCE_FILE = "attendance.csv"

# Global variables for face encodings and names
known_face_encodings = []
known_face_names = []

# Load known faces once at startup
def load_known_faces():
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    
    known_face_encodings.clear()
    known_face_names.clear()
    
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.endswith((".jpg", ".png")):
            image_path = os.path.join(KNOWN_FACES_DIR, filename)
            try:
                image = face_recognition.load_image_file(image_path)
                encoding = face_recognition.face_encodings(image, num_jitters=1)[0]
                known_face_encodings.append(encoding)
                name = os.path.splitext(filename)[0]
                known_face_names.append(name)
                print(f"Loaded face: {name} from {filename}")
            except (IndexError, Exception) as e:
                print(f"Error loading {filename}: {str(e)}")
    print(f"Total known faces loaded: {len(known_face_names)}")

# Function to log attendance
def log_attendance(name):
    with open(ATTENDANCE_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([name, date_time])
        return date_time

# Initialize attendance CSV and load faces at startup
if not os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "DateTime"])

load_known_faces()

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Registration page
@app.route('/registration')
def registration():
    return render_template('registration.html')

# Save face and name
@app.route('/save_face', methods=['POST'])
def save_face():
    name = request.form.get('name')
    image_data = request.form.get('image')
    if not name or not image_data:
        return jsonify({'success': False, 'message': 'Name and image are required'})

    try:
        image_data = base64.b64decode(image_data)
        image_array = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        save_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
        if os.path.exists(save_path):
            os.remove(save_path)
        cv2.imwrite(save_path, frame)
        
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model='cnn', number_of_times_to_upsample=1)
        if not face_locations:
            os.remove(save_path)
            return jsonify({'success': False, 'message': 'No face detected'})

        image = face_recognition.load_image_file(save_path)
        encoding = face_recognition.face_encodings(image, num_jitters=1)[0]
        known_face_encodings.append(encoding)
        known_face_names.append(name)
        
        return jsonify({'success': True, 'message': f'Successfully saved {name}'})
    except Exception as e:
        print(f"Save error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error saving: {str(e)}'})

# Attendance page
@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

# Check attendance
@app.route('/check_attendance', methods=['POST'])
def check_attendance():
    image_data = request.form.get('image')
    if not image_data:
        return jsonify({'success': False, 'message': 'Image data required'})

    try:
        image_data = base64.b64decode(image_data)
        image_array = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model='hog', number_of_times_to_upsample=1)
        
        print(f"Detected face locations: {len(face_locations)}")
        if face_locations:
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations, num_jitters=1)
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                print(f"Matches: {matches}, Distances: {face_distances}")
                if len(face_distances) > 0 and matches[np.argmin(face_distances)] and min(face_distances) < 0.6:
                    name = known_face_names[np.argmin(face_distances)]
                    date_time = log_attendance(name)
                    return jsonify({'success': True, 'message': f'Face matched: {name} at {date_time}'})
            return jsonify({'success': False, 'message': 'Unknown face detected'})
        return jsonify({'success': False, 'message': 'No face detected'})
    except Exception as e:
        print(f"Attendance check error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error processing: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)