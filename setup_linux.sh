#!/usr/bin/bash
chmod +x setup_linux.sh

# setup virtual environment
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
pip install waitress

mkdir ./app/data

flask db init
flask db migrate
flask db upgrade

echo '#!/usr/bin/bash
chmod +x run_app.sh
source ./venv/bin/activate 
exec waitress-serve --listen=*:5000 --expose-tracebacks homeroomconditions:app' > run_app.sh
