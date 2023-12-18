## Project Setup

1. Install Python - `python3.9`
2. Create a top level directory `mkdir thefuturely-workspace` and navigate to that directory `mkdir thefuturely-workspace`
3. Make sure the current working directory is `thefuturely-workspace`
4. Create a virtual environment. Run `virtualenv venv -p python3.9`
5. Activate the virtual env. Run `source venv/bin/activate`
6. Make sure you are in `thefuturely-workspace` directory. Clone the project from github. Run `git clone https://github.com/thefuturely/thefuturely`
7. Navigate to the project directory. Run `cd thefuturely/`
8. Run `pip3 install -r requirements.txt`
9. Run `python manage.py runserver`. You can see the project on your browser at `127.0.0.1:8000`


## Development guidelines
1. Pull the latest version from github. Run `git pull --rebase origin master`
2. Activate the virtual env. Run `source venv/bin/activate`
3. Install the latest requirements. Run `pip install -r requirements.txt`
4. Run the migrations to update your local snapshot. Run `python manage.py migrate`
5. Run `python manage.py runserver`. You can see the project on your browser at `127.0.0.1:8000`
6. _Make your development changes_

## Pushing your code 
1. Activate the virtual env. Run `source venv/bin/activate`
2. Run `pip freeze > requirements.txt` to collect any newly added requirements to the virtualenv.
3. Commit your changes. `git commit -am <commit msg>`
4. Push the changes to master `git push origin master`

## Work flow to update git
1. Pull the master branch. 
2. Apply changes to the code and push it to new repository.
3. Mr. Dewan will verify the repository and check for the conflicts with master branch.
4. Conflict get resolved by author.
5. At last merge it with master branch.
