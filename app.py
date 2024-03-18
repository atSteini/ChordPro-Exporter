from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import json
import os
import generate_meta
import subprocess

UPLOAD_FOLDER = ''
ALLOWED_CHO = {'txt', 'cho'}
ALLOWED_CONF = {'json'}
PORT = 5100
TO_CONVERT = '' # set in main
CONF_FILE = 'default_configfile.json'
CONF_FILE_UPLOAD = 'configfile_upload.json'
OUTPUT_FILENAME = "output.pdf"
FILES_TO_REMOVE = [CONF_FILE_UPLOAD, OUTPUT_FILENAME, "userconf.json"]

user_file = 'users.json'
file_already_downloaded = False
users = []

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
    (error, filename) = savefiles()

    if error:
      return error

    user = get_user(request.form.get('selectAuthor', None))
    version = request.form.get('version', None)

    execute_converter(OUTPUT_FILENAME, user, version)

    ret_val = send_file(open(OUTPUT_FILENAME, "rb"), mimetype='pdf', as_attachment=True, download_name=f'{filename}.pdf')

    for file in FILES_TO_REMOVE:
      if os.path.exists(file):
        os.remove(file)

    return ret_val
  
  return render_template('index.html', authors=[o['name'] for o in users])

def execute_converter(filename, user, ver):
  global CONF_FILE, CONF_FILE_UPLOAD
  
  generate_meta.generate_meta(user_initials=user["initials"][0] if user else 'N.A.',
                              version=ver)
  
  if (CONF_FILE_UPLOAD):
    CONF_FILE = CONF_FILE_UPLOAD

  subprocess.run(['chordpro', TO_CONVERT, '--config', CONF_FILE, '--output', f'{filename}'])

def get_user(name):
  for user in users:
    if user['name'] == name:
      return user
  return None

def load_users():
  global users
  print('Loading users...')
  try:
    with open(user_file, 'r') as file:
      users = json.loads(file.read())['users']

    print('Users loaded')
  except FileNotFoundError:
    print('No users file found')
  except:
    print('Error while loading users')
    raise

def allowed_file(filename, ext):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ext

def savefiles() -> tuple[str, str]:
  global file_already_downloaded, TO_CONVERT, CONF_FILE_UPLOAD

  # ChordPro File
  if 'chofile' not in request.files:
      return ('No ChordPro part', None)
    
  if file_already_downloaded:
    return ('File already downloaded', None)

  chofile = request.files['chofile']

  if chofile.filename == '':
    return ('No ChordPro File submitted', None)

  if chofile and allowed_file(chofile.filename, ALLOWED_CHO):
    filename = secure_filename(chofile.filename)
    chofile.save(TO_CONVERT)

  # Config File
  saved_conf = False
  if 'configfile' in request.files:
    configfile = request.files['configfile']
    print(configfile.filename)
    if configfile and configfile.filename != '' and allowed_file(configfile.filename, ALLOWED_CONF):
      configfile.save(CONF_FILE_UPLOAD)
      saved_conf = True

  if (not saved_conf):
    CONF_FILE_UPLOAD = None

  return (None, filename)

if __name__ == '__main__':
  TO_CONVERT = os.path.join(app.config['UPLOAD_FOLDER'], 'to_convert.cho')
  FILES_TO_REMOVE.append(TO_CONVERT)

  load_users()
  app.run(host='0.0.0.0', debug=True, port=PORT)