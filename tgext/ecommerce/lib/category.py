# coding=utf-8
from __future__ import unicode_literals
from bson import ObjectId
import tg
from tgext.ecommerce.lib.exceptions import CategoryAssignedToProductException, CategoryAcestorExistingException
from tgext.ecommerce.lib.utils import internationalise as i_, slugify_category
from tgext.ecommerce.model import models


class CategoryManager(object):

    @classmethod
    def get_ancestors_for_ops(cls, parent=None):
        ancestors = []
        if parent is not None:
            ancestors = [ancestor for ancestor in parent.ancestors]
            ancestors.append(
                dict(
                    _id=parent._id,
                    name=parent.name,
                    slug=parent.slug
                )
            )
        return ancestors

    @classmethod
    def create(cls, name, parent=None, **details):  # create_category
        if 'slug' not in details or details['slug'] == '':
            slug = slugify_category(name, models)
        else:
            slug = slugify_category(details['slug'], models)
        ancestors = CategoryManager.get_ancestors_for_ops(parent)
        category = models.Category(
            name=i_(name),
            slug=slug,
            parent=parent._id if parent else None,
            details=details,
            ancestors=ancestors)
        models.DBSession.flush()
        return category

    @classmethod
    def get(cls, _id=None, name=None, slug=None, query=None):  # get_category
        if query is None:
            query = {}
        if _id is not None and len(_id) == 24:
            query.update({'_id': ObjectId(_id)})
            return models.Category.query.find(query).first()
        if name is not None:
            name_lang = 'name.%s' % tg.config.lang
            query.update({name_lang: name})
            return models.Product.query.find(query).first()
        if slug is not None:
            query.update({'slug': slug})
            return models.Category.query.find(query).first()
        return None

    @classmethod
    def get_many(cls, query):  # get_categories
        return models.Category.query.find(query)

    @classmethod
    def get_all(cls): #get_categories
        return models.Category.query.find()

    @classmethod
    def edit(cls, _id, name, parent, **details):
        slug = slugify_category(name, models)
        ancestors = CategoryManager.get_ancestors_for_ops(parent)
        models.Category.query.update(
            {'_id': ObjectId(_id)},
            {'$set': {
                'name': i_(name),
                'slug': slug,
                'parent': parent._id if parent else None,
                'details': details,
                'ancestors': ancestors
            }})

        for cat in models.Category.query.find({'ancestors._id': ObjectId(_id)}):
            parent = models.Category.query.find({'_id': cat.parent}).first()
            if parent:
                ancestors = CategoryManager.get_ancestors_for_ops(parent)
                models.Category.query.update(
                    {'_id':cat._id},
                    {'$set': {'ancestors': ancestors}}
                )

    @classmethod
    def delete(cls, _id): #delete_category
        if models.Product.query.find({'category_id': ObjectId(_id), 'active': True}).first():
            raise CategoryAssignedToProductException('The Category is assigned to an active Product')
        if models.Category.query.find({'ancestors._id': ObjectId(_id)}).first():
            raise CategoryAcestorExistingException
        models.Category.query.get(_id=ObjectId(_id)).delete()
        models.Product.query.update({'category_id': ObjectId(_id), 'active': False},
                                    {'$set': {'category_id': None}})

    @classmethod
    def sort_up(cls, category):
        subsequent = models.Category.subsequent(category)
        try:
            little_weight = subsequent[0].sort_weight
        except:
            little_weight = 0

        try:
            big_weight = subsequent[1].sort_weight
        except:
            big_weight = little_weight + 20000

        category = models.Category.query.get(_id=ObjectId(category))
        category.sort_weight = little_weight + (big_weight-little_weight)/2

    @classmethod
    def sort_down(cls, category):
        previous = models.Category.previous(category)
        try:
            big_weight = previous[0].sort_weight
        except:
            big_weight = 0

        try:
            little_weight = previous[1].sort_weight
        except:
            little_weight = big_weight - 20000

        category = models.Category.query.get(_id=ObjectId(category))
        category.sort_weight = little_weight + (big_weight-little_weight)/2

    @classmethod
    def sort_before_other(cls, category_to_sort, other_category):
        subsequent = models.Category.subsequent(other_category._id)
        little_weight = other_category.sort_weight
        try:
            big_weight = subsequent[0].sort_weight
        except:
            big_weight = little_weight + 20000

        category_to_sort = models.Category.query.get(_id=ObjectId(category_to_sort._id))
        category_to_sort.sort_weight = little_weight + (big_weight-little_weight)/2
