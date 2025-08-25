from fastapi import APIRouter, status
from fastapi.responses import Response

auth=APIRouter(prefix="/auth", tags=["auth"])

@auth.post("/create_user")
def create_user():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@auth.post("/login")
def login():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)