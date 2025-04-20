from typing import List, Union
from pydantic import BaseModel


class Variant(BaseModel):
    name: str
    value: Union[str, List[str]]

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "Variant":
        return cls.model_validate_json(json_str)

class FeatureFlag(BaseModel):
    id: str
    variants: List[Variant]

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "FeatureFlag":
        return cls.model_validate_json(json_str)

class FeatureManagement(BaseModel):
    feature_flags: List[FeatureFlag]

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "FeatureManagement":
        return cls.model_validate_json(json_str)

class FeatureModel(BaseModel):
    schemaVersion: str
    feature_management: FeatureManagement

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "FeatureModel":
        return cls.model_validate_json(json_str)
    
    def get_variant(self, feature_flag_id: str, variant_name: str) -> str:
        for ff in self.feature_management.feature_flags:
            if ff.id == feature_flag_id:
                for v in ff.variants:
                    if v.name == variant_name:
                        return v.value
        return ""
    
    def get_variants(self, feature_flag_id: str, variant_name: str) -> List[str]:
        for ff in self.feature_management.feature_flags:
            if ff.id == feature_flag_id:
                for v in ff.variants:
                    if v.name == variant_name:
                        return v.value
        return []
