import json
from datetime import datetime
import argparse

userconf_file = "userconf.json"
major = False
initials = "N.A."
reset_version = False
update_version = False

meta = {
  "meta": {
    "initials": [initials],
    "file_ver": ["v1.0"],
    "create_time": [f"{datetime.now().strftime('%Y/%m')}"]
  }
}

parser = argparse.ArgumentParser(description="Generate meta data for the use with chordpro files")

parser.add_argument("-m", "--major", action="store_true", help="Is a major update?")
parser.add_argument("-i", "--initials", type=str, nargs=1, help="Set initials of author", default=initials)

def generate_meta(user_initials: str, version: str, is_major: bool = None, user_file: str = None, reset: bool = None, update: bool = None):
  global userconf_file, major, initials, reset_version, update_version, meta
  userconf_file = user_file if user_file else userconf_file
  major = is_major if is_major else major
  initials = user_initials if user_initials else initials
  reset_version = reset if reset else reset_version
  update_version = update if update else update_version
  meta["meta"]["file_ver"] = [version] if version else meta["meta"]["file_ver"]
  
  main()

def main():
  raised = False

  try:
    with open(userconf_file, "r") as file:
      data = json.load(file)
      
      file_ver = data["meta"]["file_ver"][0]
      if reset_version:
        file_ver = "v1.0"
        print("Resetting file version to v1.0")
      elif update_version:
        print(f"Found userconf.json file with file version {file_ver}")

        file_ver = file_ver.split(".")
        file_ver[0] = file_ver[0][1:]
        if major:
          file_ver[0] = str(int(file_ver[0]) + 1)
          file_ver[1] = "0"
        else:
          file_ver[1] = str(int(file_ver[1]) + 1)
        
        file_ver[0] = "v" + file_ver[0]
        file_ver = ".".join(file_ver)
        print(f"Setting file version to {file_ver}")
      else:
        print(f"Found userconf.json file with file version {file_ver}")
        print("No update or reset requested")

      meta["meta"]["file_ver"] = [file_ver]
      meta["meta"]["initials"] = [initials]
  except FileNotFoundError:
    print("userconf.json file not found")
    pass
  except KeyError:
    print("File version not found in userconf.json")
    pass
  except:
    print("Error while processing userconf.json")
    raised = True
    raise
  
  if raised:
    return
  
  with open(userconf_file, "w") as file:
    json.dump(meta, file, indent=2)
    print(f"Meta data generated and saved to {userconf_file}")
      
if __name__ == "__main__":
  major = parser.parse_args().major
  initials = parser.parse_args().initials

  main()