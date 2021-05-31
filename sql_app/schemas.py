import datetime
from typing import List, Optional
from pydantic import BaseModel

########################
# Shell Family Schemas #
########################
class ShellFamilyBase(BaseModel):
    pass

class ShellFamilyCreate(ShellFamilyBase):
    pass

class ShellFamily(ShellFamilyBase):
    id: int
    shell_family_id: str
    feature_extractor_model: str
    instances: int
    mapping: list
    global_mean: bytes
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class Config:
        orm_mode = True

#################
# Shell Schemas #
#################
class ShellBase(BaseModel):
    pass

class ShellCreate(ShellBase):
    pass

class Shell(ShellBase):
    id: int
    shell_family_id: str
    shell_id: str
    shell_mean: bytes
    num_instances: int
    noise_mean: float
    noise_std: float
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class Config:
        orm_mode = True
    

########################
# Shell Images Schemas #
########################
class ShellImagesBase(BaseModel):
    pass

class ShellImagesCreate(ShellImagesBase):
    pass

class ShellImages(ShellImagesBase):
    id: int
    shell_family_id: str
    shell_id: str
    image_path = str
    image_features = bytes
    assigned_at = datetime.datetime
    class Config:
        orm_mode = True

##################
# Images Schemas #
##################
class ImagesBase(BaseModel):
    pass

class ImagesCreate(ImagesBase):
    pass

class Images(ImagesBase):
    id: int
    image_class = str
    image_path = str
    uploaded_at = datetime.datetime
    class Config:
        orm_mode = True