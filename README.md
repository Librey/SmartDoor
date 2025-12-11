 SmartDoor: Raspberry Pi Secure Door Lock System

This repository contains my CSC 6370 Smart Door Lock Project, built using a Raspberry Pi, servo motor, RFID module, keypad, buzzer, and a Flask web interface.  
The system allows locking/unlocking the door from multiple sources: RFID tag, password, keypad input, or the admin web page.

🚪 Project Features

1. RFID Authentication
Unlocks the door when a registered RFID tag is detected.
Logs every access attempt.

2. Keypad Input
Users can type in a PIN.
Correct PIN unlocks; incorrect attempts are logged.

3. Web Interface (Flask App)
Accessible through the Pi’s IP address:
`/` → Enter password  
 `/admin` → View logs & change password  
`/change_password` → Update system password  

4. Servo Motor Control
Rotates to lock/unlock the door mechanism.

5. Event Logging
All activity is recorded in:
logs/events.log

6. Password Storage
System password is stored in:

password.txt




 🗂 Project Structure

SmartDoor/
 │
 ├── smart_door.py  Main Python program (RFID, keypad, servo, buzzer, Flask)
 ├── password.txt Stores current system password
 ├── logs/
 │ └── events.log  Activity log file
 │
 ├── templates/ HTML files for Flask interface
 │ ├── index.html
 │ ├── unlocked.html
 │ ├── locked.html
 │ ├── admin.html
 │ └── change_password.html


▶️ Running the Project

Start the smart door system:
python3 smart_door.py

Then visit the web interface:
http://<your_pi_ip>:5000
Example:

http://100.70.90.28:5000


📦 Hardware Used
 Raspberry Pi 4  
 MFRC522 RFID module  
 SG90 Servo motor  
 4×4 Matrix keypad  
 Active buzzer  
 Jumper wires + breadboard  
 USB power supply  

 👤 Author
Liberty Ikpeogu
Georgia State University CSC 6370  
GitHub: Librey


🎥 Demo Video
A link will be added when uploaded

📌 Notes
This repo is mainly for academic submission.  
The Raspberry Pi will be returned, so the code is preserved here for grading and future reference.
