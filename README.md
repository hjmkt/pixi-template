# pixi-template

## Setup

```bash
git clone https://github.com/hjmkt/pixi-template.git
cd pixi-template
pyenv install 3.9.1
pyenv global 3.9.1
pipenv install
pipenv shell

# For development
sudo apt install npm
sudo npm install yarn -g
```

## Run

```bash
python main.py # open http://localhost:18150/
```

## Build frontend

```bash
cd frontend
yarn # run only once
./node_modules/.bin/webpack --mode development # compiled bundle.js should be generated under flask/public/static/js

