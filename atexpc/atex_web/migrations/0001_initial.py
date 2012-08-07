# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Product'
        db.create_table('atex_web_product', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('atex_web', ['Product'])

        # Adding model 'Image'
        db.create_table('atex_web_image', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Product'], null=True, on_delete=models.SET_NULL)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('image', self.gf('sorl.thumbnail.fields.ImageField')(max_length=128)),
        ))
        db.send_create_signal('atex_web', ['Image'])


    def backwards(self, orm):
        # Deleting model 'Product'
        db.delete_table('atex_web_product')

        # Deleting model 'Image'
        db.delete_table('atex_web_image')


    models = {
        'atex_web.image': {
            'Meta': {'object_name': 'Image'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '128'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['atex_web.Product']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        'atex_web.product': {
            'Meta': {'object_name': 'Product'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['atex_web']