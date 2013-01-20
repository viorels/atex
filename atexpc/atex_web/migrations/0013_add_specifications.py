# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SpecificationGroup'
        db.create_table('atex_web_specificationgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('atex_web', ['SpecificationGroup'])

        # Adding model 'Specification'
        db.create_table('atex_web_specification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.SpecificationGroup'], null=True)),
        ))
        db.send_create_signal('atex_web', ['Specification'])

        # Adding model 'ProductSpecification'
        db.create_table('atex_web_productspecification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Product'])),
            ('spec', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Specification'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('atex_web', ['ProductSpecification'])


    def backwards(self, orm):
        # Deleting model 'SpecificationGroup'
        db.delete_table('atex_web_specificationgroup')

        # Deleting model 'Specification'
        db.delete_table('atex_web_specification')

        # Deleting model 'ProductSpecification'
        db.delete_table('atex_web_productspecification')


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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'specs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['atex_web.Specification']", 'through': "orm['atex_web.ProductSpecification']", 'symmetrical': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'atex_web.productspecification': {
            'Meta': {'object_name': 'ProductSpecification'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['atex_web.Product']"}),
            'spec': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['atex_web.Specification']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'atex_web.specification': {
            'Meta': {'object_name': 'Specification'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['atex_web.SpecificationGroup']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'atex_web.specificationgroup': {
            'Meta': {'object_name': 'SpecificationGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['atex_web']