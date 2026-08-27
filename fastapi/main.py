from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from subapp import subapp

app = FastAPI(title="App Principal")


@app.get("/")
def read_root():
    return {"message": "Estou na aplicacao principal", "app": "main"}


@app.get("/info")
def info():
    return {"routes": [route.path for route in app.routes]}


# Monta a sub-aplicacao inteira em /subapp
# Tudo que a subapp define em / passa a responder em /subapp/...
app.mount("/subapp", subapp)

# Monta um diretorio de arquivos estaticos em /static
app.mount("/static", StaticFiles(directory="static"), name="static")
