# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Dropbox.delta_cursor'
        db.alter_column('atex_web_dropbox', 'delta_cursor', self.gf('django.db.models.fields.CharField')(max_length=512, null=True))

    def backwards(self, orm):

        # Changing field 'Dropbox.delta_cursor'
        db.alter_column('atex_web_dropbox', 'delta_cursor', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

    models = {
        'atex_web.dropbox': {
            'Meta': {'object_name': 'Dropbox'},
            'app_key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'primary_key': 'True'}),
            'delta_cursor': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'})
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['atex_web']