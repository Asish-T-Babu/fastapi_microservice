import enum

class GenderCategoryEnum(enum.Enum):
    MAN = 1
    WOMAN = 2
    TRANS_GENDER = 3

class RoleEnum(enum.Enum):
    USER = 1
    ADMIN = 2
    SUPER_ADMIN = 3