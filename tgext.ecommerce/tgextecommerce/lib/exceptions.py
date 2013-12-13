class ProductException(Exception):
    pass


class AlreadyExistingSlugException(ProductException):
    pass


class AlreadyExistingSkuException(ProductException):
    pass