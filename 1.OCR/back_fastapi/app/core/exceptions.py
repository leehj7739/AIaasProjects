from fastapi import HTTPException

class OCRException(HTTPException):
    """OCR 처리 관련 예외"""
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=detail)

class GPTException(HTTPException):
    """GPT 처리 관련 예외"""
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=detail)

class FileValidationException(HTTPException):
    """파일 검증 관련 예외"""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail) 