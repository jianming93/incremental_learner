from PIL import Image
import pickle

import numpy as np
from sqlalchemy import and_, or_, not_, desc
from sqlalchemy.orm import Session
from . import models, schemas

#####################
# Shell Family CRUD #
#####################
def get_shell_family(db: Session, id: int):
    return db.query(models.ShellFamily).filter(models.ShellFamily.id == id).first()

def get_shell_family_by_shell_family_id(db: Session, shell_family_id: str):
    return db.query(models.ShellFamily).filter(models.ShellFamily.shell_family_id == shell_family_id).first()

def get_shell_families(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ShellFamily).offset(skip).limit(limit).all()

def create_shell_family(db: Session, shell_family_id: str, feature_extractor_model: str, instances: int, mapping: list, global_mean: float):
    db_shell_family = models.ShellFamily(shell_family_id=shell_family_id,
                                         feature_extractor_model=feature_extractor_model,
                                         instances=instances,
                                         mapping=mapping,
                                         global_mean=global_mean)
    db.add(db_shell_family)
    db.commit()
    db.refresh(db_shell_family)
    return db_shell_family

def update_shell_family(db: Session, shell_family_id: str, feature_extractor_model: str, instances: int, mapping: list, global_mean: np.ndarray, updated_at: str):
    db_shell_family_to_update = db.query(models.ShellFamily).filter(models.ShellFamily.shell_family_id == shell_family_id).first()
    db_shell_family_to_update.feature_extractor_model = feature_extractor_model
    db_shell_family_to_update.instances = instances
    db_shell_family_to_update.mapping = mapping
    db_shell_family_to_update.global_mean = global_mean
    db_shell_family_to_update.updated_at = updated_at
    db.commit()
    db.refresh(db_shell_family_to_update)
    return db_shell_family_to_update

def delete_shell_family(db: Session, shell_family_id: str):
    db.query(models.ShellFamily).filter(models.ShellFamily.shell_family_id == shell_family_id).delete()
    db.commit()
    return True


##############
# Shell CRUD #
##############
def get_shell(db: Session, id: int):
    return db.query(models.Shell).filter(models.Shell.id == id).first()

def get_shell_by_shell_id(db: Session, shell_id: int):
    return db.query(models.Shell).filter(models.Shell.shell_id == shell_id).first()

def get_all_shell_families_and_their_shells(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Shell).offset(skip).limit(limit).all()

def get_all_shells_by_shell_family_id(db: Session, shell_family_id: str):
    return db.query(models.Shell).filter(models.Shell.shell_family_id == shell_family_id).all()

def create_shell_for_shell_family(db: Session, shell_family_id: str, shell_id: str, shell_mean:float, num_instances: int, noise_mean: float, noise_std: float):
    db_shell = models.Shell(shell_family_id=shell_family_id,
                            shell_id=shell_id,
                            shell_mean=shell_mean,
                            num_instances=num_instances,
                            noise_mean=noise_mean,
                            noise_std=noise_std)
    db.add(db_shell)
    db.commit()
    db.refresh(db_shell)
    return db_shell

def update_shell_for_shell_family(db: Session, shell_family_id: str, shell_id: str, shell_mean:float, num_instances: int, noise_mean: float, noise_std: float, updated_at):
    db_shell_to_update = db.query(models.Shell).filter(and_(models.Shell.shell_family_id == shell_family_id, models.Shell.shell_id == shell_id)).first()
    db_shell_to_update.shell_mean = shell_mean
    db_shell_to_update.num_instances = num_instances
    db_shell_to_update.noise_mean = noise_mean
    db_shell_to_update.noise_std = noise_std
    db_shell_to_update.updated_at = updated_at
    db.commit()
    db.refresh(db_shell_to_update)
    return db_shell_to_update

def bulk_create_shells_for_shell_family(db: Session, shell_family_id: str, shell_id_list: list, shell_mean_list:float, num_instances_list: int, noise_mean_list: float, noise_std_list: float):
    db.bulk_insert_mappings(
        models.Shell,
        [
            dict(
                shell_family_id=shell_family_id,
                shell_id=shell_id_list[i],
                shell_mean=shell_mean_list[i],
                num_instances=num_instances_list[i],
                noise_mean=noise_mean_list[i],
                noise_std=noise_std_list[i]
            ) for i in range(len(shell_id_list))
        ]
    )
    db.commit()
    return True

def delete_shell_for_shell_family(db: Session, shell_family_id: str, shell_id: str):
    db.query(models.Shell).filter(and_(models.Shell.shell_family_id == shell_family_id, models.Shell.shell_id == shell_id)).delete()
    db.commit()
    return True


#####################
# Shell Images CRUD #
#####################
def get_shell_images(db: Session, id: int):
    return db.query(models.ShellImages).filter(models.ShellImages.id == id).first()

def get_all_shell_images_by_shell_family_id_and_shell_id(db: Session, shell_family_id: str, shell_id: str):
    return db.query(models.ShellImages).filter(
        and_(
            models.ShellImages.shell_family_id == shell_family_id,
            models.ShellImages.shell_id == shell_id
            )
        ).all()

def get_latest_shell_image_by_shell_family_id(db: Session, shell_family_id: str):
    return db.query(models.ShellImages).filter(
        models.ShellImages.shell_family_id == shell_family_id
        ).order_by(desc('assigned_at')).first()

def get_latest_shell_image_by_shell_family_id_and_shell_id(db: Session, shell_family_id: str, shell_id: str):
    return db.query(models.ShellImages).filter(
        and_(
            models.ShellImages.shell_family_id == shell_family_id,
            models.ShellImages.shell_id == shell_id
            )
        ).order_by(desc('assigned_at')).first()


def get_all_shell_images_by_shell_family_id_and_shell_id_with_no_image_features(db: Session, shell_family_id: str, shell_id: str):
    return db.query(models.ShellImages).filter(
        and_(
            models.ShellImages.shell_family_id == shell_family_id,
            models.ShellImages.shell_id == shell_id,
            models.ShellImages.image_features.is_(None)
            )
        ).all()

def get_all_shell_images(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ShellImages).offset(skip).limit(limit).all()
    
def create_shell_images(db: Session, shell_family_id: str, shell_id: str, image_path: str, image_features: bytes, assigned_at):
    db_shell_images = models.ShellImages(shell_family_id=shell_family_id, shell_id=shell_id, image_path=image_path, image_features=image_features, assigned_at=assigned_at)
    db.add(db_shell_images)
    db.commit()
    db.refresh(db_shell_images)
    return db_shell_images

def bulk_create_shell_images_for_one_shell_family(db: Session, shell_family_id: str, class_name_array: str, image_path_list: list, image_features_list: bytes):
    db.bulk_insert_mappings(
        models.ShellImages,
        [
            dict(
                shell_family_id=shell_family_id,
                shell_id=class_name_array[i],
                image_path=image_path_list[i],
                image_features=image_features_list[i]
            ) for i in range(len(image_path_list))
        ]
    )
    db.commit()
    return True


def update_all_shell_images_by_shell_family_id_and_shell_id_with_no_image_features(db: Session, shell_family_id: str, shell_id: str, shell_family, target_size: int, update_datetime):
    shell_images_to_update = db.query(models.ShellImages).filter(
        and_(
            models.ShellImages.shell_family_id == shell_family_id,
            models.ShellImages.shell_id == shell_id,
            models.ShellImages.image_features.is_(None)
        )).all()
    for shell_image in shell_images_to_update:
        shell_image.image_features = image_path_to_image_features(shell_image.image_path, shell_family, target_size)
        shell_image.assigned_at = update_datetime
    db.commit()
    return True


def delete_shell_image(db: Session, shell_family_id: str, shell_id: str, image_path: str):
    db.query(models.ShellImages).filter(
        and_(
            models.ShellImages.shell_family_id == shell_family_id,
            models.ShellImages.shell_id == shell_id,
            models.ShellImages.image_path == image_path
        )
    ).delete()
    db.commit()
    return True


def delete_all_shell_images_by_shell_family_id_and_shell_id(db: Session, shell_family_id: str, shell_id: str):
    db.query(models.ShellImages).filter(
        and_(
            models.ShellImages.shell_family_id == shell_family_id,
            models.ShellImages.shell_id == shell_id
        )
    ).delete()
    db.commit()
    return True


###############
# Images CRUD #
###############
def get_image(db: Session, id: int):
    return db.query(models.Images).filter(models.Images.id == id).first()

def get_image_by_image_path(db: Session, image_path: str):
    return db.query(models.Images).filter(models.Images.image_path == image_path).first()

def get_all_images(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Images).offset(skip).limit(limit).all()

def create_image(db: Session, image_class:str, image_path: str):
    db_images = models.Images(image_class=image_class, image_path=image_path)
    db.add(db_images)
    db.commit()
    db.refresh(db_images)
    return db_images

def bulk_create_images(db: Session, image_class_list: list, image_path_list: list):
    db.bulk_insert_mappings(
        models.Images,
        [
            dict(image_class=image_class_list[i], image_path=image_path_list[i]) for i in range(len(image_class_list)) 
        ]
    )
    db.commit()
    return True


def delete_image(db: Session, image_path: str):
    db.query(models.Images).filter(models.Images.image_path == image_path).delete()
    db.commit()
    return True


###################
# Helper Function #
###################
def image_path_to_image_features(image_path, shell_family, target_size):
    with Image.open(image_path).convert("RGB") as img:
        resized_img = img.resize((target_size, target_size))
        resized_img_array = np.array(resized_img)
        expanded_resized_img_array = np.expand_dims(resized_img_array, 0)
        preprocessed_img_array = shell_family.preprocessor_preprocess_function(expanded_resized_img_array)
        sample_features = shell_family.preprocessor.predict(preprocessed_img_array)
    return pickle.dumps(sample_features[0])
