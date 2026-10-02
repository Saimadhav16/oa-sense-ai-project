import uvicorn

if __name__ == "__main__":
    print("============================================================")
    print("Starting OA-Sense AI Backend Server...")
    print("Docs available at: http://127.0.0.1:8000/docs")
    print("Health check:     http://127.0.0.1:8000/health")
    print("============================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
