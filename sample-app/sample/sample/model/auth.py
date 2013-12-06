# -*- coding: utf-8 -*-
"""
Auth* related model.

This is where the models used by the authentication stack are defined.

It's perfectly fine to re-use this definition in the sample application,
though.

"""
import os
from datetime import datetime
from hashlib import sha256
__all__ = ['User', 'Group', 'Permission']

from ming import schema as s
from ming.orm import FieldProperty, ForeignIdProperty, RelationProperty
from ming.orm import Mapper
from ming.orm.declarative import MappedClass
from tgming import SynonymProperty, ProgrammaticRelationProperty
from session import DBSession

class Group(MappedClass):
    """
    Group definition.
    """
    class __mongometa__:
        session = DBSession
        name = 'tg_group'
        unique_indexes = [('group_name',),]

    _id = FieldProperty(s.ObjectId)
    group_name = FieldProperty(s.String)
    display_name = FieldProperty(s.String)

    def _get_permissions(self):
        return Permission.query.find(dict(_groups=self.group_name)).all()
    def _set_permissions(self, value):
        current_permissions = self.permissions
        #erase removed permissions
        for perm in current_permissions:
            if perm not in value:
                perm._groups = list(set(perm._groups) - set([self.group_name]))
        #set added permissions
        for perm in value:
            if perm not in current_permissions:
                perm._groups = list(set([self.group_name]) | set(perm._groups))
    permissions = ProgrammaticRelationProperty('Permission', _get_permissions, _set_permissions)

class Permission(MappedClass):
    """
    Permission definition.
    """
    class __mongometa__:
        session = DBSession
        name = 'tg_permission'
        unique_indexes = [('permission_name',),]

    _id = FieldProperty(s.ObjectId)
    permission_name = FieldProperty(s.String)
    description = FieldProperty(s.String)

    _groups = FieldProperty(s.Array(str))

    def _get_groups(self):
        return Group.query.find(dict(group_name={'$in':self._groups})).all()
    def _set_groups(self, groups):
        self._groups = [group.group_name for group in groups]
    groups = ProgrammaticRelationProperty(Group, _get_groups, _set_groups)

class User(MappedClass):
    """
    User definition.

    This is the user definition used by :mod:`repoze.who`, which requires at
    least the ``user_name`` column.

    """
    class __mongometa__:
        session = DBSession
        name = 'tg_user'
        unique_indexes = [('user_name',),]

    _id = FieldProperty(s.ObjectId)
    user_name = FieldProperty(s.String)
    email_address = FieldProperty(s.String)
    display_name = FieldProperty(s.String)

    _groups = FieldProperty(s.Array(str))

    _password = FieldProperty(s.String)
    created = FieldProperty(s.DateTime, if_missing=datetime.now)

    def _get_groups(self):
        return Group.query.find(dict(group_name={'$in':self._groups})).all()
    def _set_groups(self, groups):
        self._groups = [group.group_name for group in groups]
    groups = ProgrammaticRelationProperty(Group, _get_groups, _set_groups)

    @property
    def permissions(self):
        return Permission.query.find(dict(_groups={'$in':self._groups})).all()

    @classmethod
    def by_email_address(cls, email):
        """Return the user object whose email address is ``email``."""
        return cls.query.get(email_address=email)

    @classmethod
    def _hash_password(cls, password):
        salt = sha256()
        salt.update(os.urandom(60))
        salt = salt.hexdigest()

        hash = sha256()
        # Make sure password is a str because we cannot hash unicode objects
        hash.update((password + salt).encode('utf-8'))
        hash = hash.hexdigest()

        password = salt + hash

        # Make sure the hashed password is a unicode object at the end of the
        # process because SQLAlchemy _wants_ unicode objects for Unicode cols
        password = password.decode('utf-8')

        return password

    def _set_password(self, password):
        """Hash ``password`` on the fly and store its hashed version."""
        self._password = self._hash_password(password)

    def _get_password(self):
        """Return the hashed version of the password."""
        return self._password

    password = SynonymProperty(_get_password, _set_password)

    def validate_password(self, password):
        """
        Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool

        """
        hash = sha256()
        hash.update((password + self.password[:64]).encode('utf-8'))
        return self.password[64:] == hash.hexdigest()
