from .. import app, xbot


@app.on_event("startup")
async def startup_event():
    await xbot.start()


@app.on_event("shutdown")
async def shutdown():
    await xbot.stop()
