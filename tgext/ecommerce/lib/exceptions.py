class EcommerceException(Exception):
    pass


class ProductException(EcommerceException):
    pass


class AlreadyExistingSlugException(ProductException):
    pass


class AlreadyExistingSkuException(ProductException):
    pass


class CategoryAssignedToProductException(ProductException):
    pass


class InactiveProductException(ProductException):
    pass


class CartException(EcommerceException):
    pass


class CartLockedException(CartException):
    pass