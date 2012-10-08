# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Hit'
        db.create_table('atex_web_hit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Product'])),
            ('count', self.gf('django.db.models.fields.IntegerField')()),
            ('date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('atex_web', ['Hit'])


    def backwards(self, orm):
        # Deleting model 'Hit'
        db.delete_table('atex_web_hit')


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
            'ancora_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        }
    }

    complete_apps = ['atex_web']