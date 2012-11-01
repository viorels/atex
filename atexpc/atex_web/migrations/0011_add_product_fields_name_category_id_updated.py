# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.utils.timezone import now

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Product.name'
        db.add_column('atex_web_product', 'name',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255),
                      keep_default=False)

        # Adding field 'Product.category_id'
        db.add_column('atex_web_product', 'category_id',
                      self.gf('django.db.models.fields.IntegerField')(null=True),
                      keep_default=False)

        # Adding field 'Product.updated'
        db.add_column('atex_web_product', 'updated',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, default=now(), blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Product.name'
        db.delete_column('atex_web_product', 'name')

        # Deleting field 'Product.category_id'
        db.delete_column('atex_web_product', 'category_id')

        # Deleting field 'Product.updated'
        db.delete_column('atex_web_product', 'updated')


    models = {
        'atex_web.dropbox': {
            'Meta': {'object_name': 'Dropbox'},
            'app_key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'primary_key': 'True'}),
            'delta_cursor': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'atex_web.hit': {
            'Meta': {'object_name': 'Hit'},
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['atex_web.Product']"})
        },
        'atex_web.image': {
            'Meta': {'object_name': 'Image'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '255'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['atex_web.Product']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        'atex_web.product': {
            'Meta': {'object_name': 'Product'},
            'category_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['atex_web']