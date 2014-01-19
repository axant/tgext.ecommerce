
class ProductException(Exception):
    pass


class AlreadyExistingSlugException(ProductException):
    pass


class AlreadyExistingSkuException(ProductException):
    pass


class CategoryAssignedToProductException(ProductException):
    pass


class InactiveProductException(ProductException):
    pass