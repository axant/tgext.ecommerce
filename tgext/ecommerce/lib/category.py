# coding=utf-8
from __future__ import unicode_literals
from bson import ObjectId
import tg
from tgext.ecommerce.lib.exceptions import CategoryAssignedToProductException
from tgext.ecommerce.lib.utils import slugify, internationalise as i_, NoDefault
from tgext.ecommerce.model import models


class CategoryManager(object):

    @classmethod
    def create(cls, name): #create_category
        category = models.Category(name=i_(name))
        models.DBSession.flush()
        return category

    @classmethod
    def get(cls, _id=None, name=None): #get_category
        if _id:
            return models.Category.query.get(_id=ObjectId(_id))
        name_lang = 'name.%s' % tg.config.lang
        return models.Category.query.find({name_lang: name}).first()

    @classmethod
    def get_all(cls): #get_categories
        return models.Category.query.find()

    @classmethod
    def delete(cls, _id): #delete_category
        if models.Product.query.find({'category_id': ObjectId(_id), 'active': True}).first():
            raise CategoryAssignedToProductException('The Category is assigned to an active Product')

        models.Category.query.get(_id=ObjectId(_id)).delete()
        models.Product.query.update({'category_id': ObjectId(_id), 'active': False},
                                    {'$set': {'category_id': None}})