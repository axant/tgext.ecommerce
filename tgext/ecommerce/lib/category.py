# coding=utf-8
from __future__ import unicode_literals
from bson import ObjectId
import tg
from tgext.ecommerce.lib.exceptions import CategoryAssignedToProductException
from tgext.ecommerce.lib.utils import slugify, internationalise as i_, NoDefault, slugify_category
from tgext.ecommerce.model import models


class CategoryManager(object):

    @classmethod
    def create(cls, name, parent=None): #create_category
        slug = slugify_category(name, models)
        ancestors = []
        parent_id = None
        if parent is not None:
            ancestors = [ancestor for ancestor in parent.ancestors]
            ancestors.append(dict(_id=parent._id, name=parent.name, slug=parent.slug))
            parent_id = parent._id
        category = models.Category(name=i_(name), slug=slug, parent=parent_id, ancestors=ancestors)
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
    def edit(cls, _id, name, parent):
        slug = slugify_category(name, models)
        ancestors = []
        parent_id = None
        if parent is not None:
            ancestors = [ancestor for ancestor in parent.ancestors]
            ancestors.append(dict(_id=parent._id, name=parent.name, slug=parent.slug))
            parent_id = parent._id
        models.Category.query.update({'_id': ObjectId(_id)},
                                     {'$set': {'name': i_(name),
                                               'slug': slug,
                                               'parent': parent_id,
                                               'ancestors': ancestors}})

        models.Category.query.update({'ancestors._id': ObjectId(_id)},
                                     {'$set': {'ancestors.$.name': i_(name), 'ancestors.$.slug': slug}}, multi=True)


    @classmethod
    def delete(cls, _id): #delete_category
        if models.Product.query.find({'category_id': ObjectId(_id), 'active': True}).first():
            raise CategoryAssignedToProductException('The Category is assigned to an active Product')

        models.Category.query.get(_id=ObjectId(_id)).delete()
        models.Product.query.update({'category_id': ObjectId(_id), 'active': False},
                                    {'$set': {'category_id': None}})