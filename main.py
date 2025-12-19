import uvicorn

if __name__ == "__main__":
    uvicorn.run(app="app.app:app", host="0.0.0.0", port=8000, reload=True)
    # "app.app:app" -> directory.file:function
    # when host="0.0.0.0", it say run it on any available domain which is localhost as well as Private IP address of machine
