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
CONF_FILE_LYRICS_ONLY = 'lyrics_only_config.json'
CONF_FILE_UPLOAD = 'configfile_upload.json'
OUTPUT_FILENAME = "output.pdf"
FILES_TO_REMOVE = [CONF_FILE_UPLOAD, OUTPUT_FILENAME, "userconf.json"]

user_file = 'users.json'
file_already_downloaded = False
users = []
default_user = {"name": "N.A.", "initials": ["N.A."]}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def convert():
  if request.method == 'POST':
    (error, filename) = savefiles()

    if error:
      return error

    user = get_user(request.form.get('selectAuthor', None))
    version = request.form.get('version', None)
    lyrics_only = request.form.get('lyricsOnlyChbx', None)

    execute_converter(OUTPUT_FILENAME, user, version, lyrics_only)

    ret_val = send_file(open(OUTPUT_FILENAME, "rb"), mimetype='pdf', as_attachment=True, download_name=f'{filename}.pdf')

    for file in FILES_TO_REMOVE:
      if os.path.exists(file):
        os.remove(file)

    return ret_val
  
  return render_template('index.html', authors=[o['name'] for o in users])

def execute_converter(filename, user, ver, lyrics_only):
  global CONF_FILE, CONF_FILE_UPLOAD, default_user

  user_to_use = user if user else default_user
  print(user_to_use)
  generate_meta.generate_meta(user_initials=user_to_use["initials"][0],
                              version=ver)
  
  if (CONF_FILE_UPLOAD):
    CONF_FILE = CONF_FILE_UPLOAD

  command = ['chordpro', TO_CONVERT, '--config', CONF_FILE, '--output', f'{filename}']

  if lyrics_only:
    command += (['--lyrics-only', '--config', CONF_FILE_LYRICS_ONLY])

  subprocess.run(command)

def get_user(name):
  for user in users:
    if user['name'] == name:
      return user
  return None

def load_users():
  global users, default_user
  print('Loading users...')
  try:
    with open(user_file, 'r') as file:
      users = json.loads(file.read())['users']
      for user in users:
        if 'is_default' in user:
          default_user = user

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

  by_text = False

  if request.form.get('choTextInput', None):
    by_text = True
    with open(TO_CONVERT, 'w') as file:
      file.write(request.form.get('choTextInput', None))
    #file_already_downloaded = True
    filename = 'text'

  # ChordPro File
  if not by_text and 'chofile' not in request.files:
      return ('No ChordPro part', None)
    
  if not by_text and file_already_downloaded:
    return ('File already downloaded', None)

  if not by_text:
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