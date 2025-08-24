from fastapi import APIRouter, status
from fastapi.responses import Response

auth=APIRouter(prefix="/auth", tags=["auth"])

@auth.post("/sign_up")
def sign_up():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@auth.post("/login")
def login():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)