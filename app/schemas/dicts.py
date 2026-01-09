from pydantic import BaseModel

class DictItem(BaseModel):
    code: str
    name: str

class MedicationItem(BaseModel):
    code: str
    name: str
    form: str
