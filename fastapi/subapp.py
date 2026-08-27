from fastapi import FastAPI

subapp = FastAPI(title="Sub Aplicacao")


@subapp.get("/")
def read_root():
    return {"message": "Estou na sub-aplicacao", "app": "subapp"}


@subapp.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Ola, {name}! Voce esta na subapp."}
