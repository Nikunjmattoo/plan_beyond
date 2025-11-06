def success(result, message="Success"):
    return {"status_code": 200, "status": "success", "message": message, "result": result}

# def success_with_data(result, message="Success", data={}):
#     return {"status_code": 200, "status": "success", "message": message, "result": result, "total_count" : data}

def error(code=400, message="Error"):
    return {"status_code": code, "status": "error", "message": message, "result": {}}