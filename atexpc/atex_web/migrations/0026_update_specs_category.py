# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from atexpc.atex_web.ancora_api import AncoraAPI


class Migration(DataMigration):

    def forwards(self, orm):
        self.synchronize_categories(orm)
        for spec in orm.Specification.objects.all():
            if spec.product_set.count() > 0:
                category_ids = [p.category_id for p in spec.product_set.distinct('category_id')]
                last_category_id = category_ids.pop()
                spec.category = orm.Category.objects.get(id=last_category_id)
                spec.save()
                for category_id in category_ids:
                    spec_copy = orm.Specification(name=spec.name,
                                                  group=spec.group,
                                                  category_id=category_id)
                    spec_copy.save()
                    orm.ProductSpecification.objects \
                                            .filter(spec=spec, 
                                                    product__category_id=425) \
                                            .update(spec=spec_copy)
            else:
                spec.delete()

        for spec_group in orm.SpecificationGroup.objects.all():
            category = spec_group.specification_set.first().category
            spec_group.category = category
            spec_group.save()

    def synchronize_categories(self, orm):
        api = AncoraAPI(api_timeout=300)
        for category in api.categories.get_all():
            parent = api.categories.get_parent_category(category['id'])
            parent_id = parent['id'] if parent is not None else None
            try:
                category_store = orm.Category.objects.get(id=category['id'])
            except orm.Category.DoesNotExist:
                orm.Category.objects.create(id=category['id'],
                                            name=category['name'],
                                            code=category['code'],
                                            parent_id=parent_id)

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'atex_web.cart': {
            'Meta': {'object_name': 'Cart'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['atex_web.Product']", 'through': u"orm['atex_web.CartProducts']", 'symmetrical': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sessions.Session']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.CustomUser']", 'null': 'True'})
        },
        u'atex_web.cartproducts': {
            'Meta': {'object_name': 'CartProducts'},
            'cart': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Cart']"}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Product']"})
        },
        u'atex_web.category': {
            'Meta': {'object_name': 'Category'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Category']", 'null': 'True'})
        },
        u'atex_web.customuser': {
            'Meta': {'object_name': 'CustomUser'},
            'ancora_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"})
        },
        u'atex_web.dropbox': {
            'Meta': {'object_name': 'Dropbox'},
            'app_key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'primary_key': 'True'}),
            'delta_cursor': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'})
        },
        u'atex_web.hit': {
            'Meta': {'unique_together': "(('product', 'date'),)", 'object_name': 'Hit'},
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Product']"})
        },
        u'atex_web.image': {
            'Meta': {'object_name': 'Image'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '255'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Product']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        u'atex_web.product': {
            'Meta': {'object_name': 'Product'},
            'category_id': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'specs': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['atex_web.Specification']", 'through': u"orm['atex_web.ProductSpecification']", 'symmetrical': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        u'atex_web.productspecification': {
            'Meta': {'object_name': 'ProductSpecification'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Product']"}),
            'spec': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Specification']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'atex_web.specification': {
            'Meta': {'object_name': 'Specification'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Category']", 'null': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.SpecificationGroup']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'atex_web.specificationgroup': {
            'Meta': {'object_name': 'SpecificationGroup'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Category']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'sessions.session': {
            'Meta': {'object_name': 'Session', 'db_table': "'django_session'"},
            'expire_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'session_data': ('django.db.models.fields.TextField', [], {}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'primary_key': 'True'})
        }
    }

    complete_apps = ['atex_web']
    symmetrical = True
