import os

appdata = os.environ.get('APPDATA')
userprofile = os.environ.get('USERPROFILE')

paths = []
if appdata:
    paths.append(os.path.join(appdata, "postgresql", "pgpass.conf"))
if userprofile:
    paths.append(os.path.join(userprofile, "AppData", "Roaming", "postgresql", "pgpass.conf"))
    paths.append(os.path.join(userprofile, "_pgpass"))
    paths.append(os.path.join(userprofile, ".pgpass"))

for p in paths:
    if os.path.exists(p):
        print(f"Found pgpass file at: {p}")
        try:
            with open(p, 'r') as f:
                print(f"Content:")
                print(f.read())
        except Exception as e:
            print(f"Failed to read: {e}")
    else:
        print(f"Not found: {p}")
