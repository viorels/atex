# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Category'
        db.create_table(u'atex_web_category', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Category'], null=True)),
            ('specs_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True)),
        ))
        db.send_create_signal(u'atex_web', ['Category'])

        # Adding model 'Product'
        db.create_table(u'atex_web_product', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=128, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Category'], null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'atex_web', ['Product'])

        # Adding model 'Image'
        db.create_table(u'atex_web_image', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Product'], null=True, on_delete=models.SET_NULL)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=128, db_index=True)),
            ('image', self.gf('sorl.thumbnail.fields.ImageField')(max_length=255)),
        ))
        db.send_create_signal(u'atex_web', ['Image'])

        # Adding model 'Hit'
        db.create_table(u'atex_web_hit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Product'])),
            ('count', self.gf('django.db.models.fields.IntegerField')()),
            ('date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal(u'atex_web', ['Hit'])

        # Adding unique constraint on 'Hit', fields ['product', 'date']
        db.create_unique(u'atex_web_hit', ['product_id', 'date'])

        # Adding model 'CustomUser'
        db.create_table(u'atex_web_customuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75, db_index=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('ancora_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'atex_web', ['CustomUser'])

        # Adding M2M table for field groups on 'CustomUser'
        m2m_table_name = db.shorten_name(u'atex_web_customuser_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customuser', models.ForeignKey(orm[u'atex_web.customuser'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['customuser_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'CustomUser'
        m2m_table_name = db.shorten_name(u'atex_web_customuser_user_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customuser', models.ForeignKey(orm[u'atex_web.customuser'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['customuser_id', 'permission_id'])

        # Adding model 'Cart'
        db.create_table(u'atex_web_cart', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sessions.Session'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.CustomUser'], null=True)),
        ))
        db.send_create_signal(u'atex_web', ['Cart'])

        # Adding model 'CartProducts'
        db.create_table(u'atex_web_cartproducts', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cart', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Cart'])),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Product'])),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal(u'atex_web', ['CartProducts'])

        # Adding model 'Dropbox'
        db.create_table(u'atex_web_dropbox', (
            ('app_key', self.gf('django.db.models.fields.CharField')(max_length=64, primary_key=True)),
            ('delta_cursor', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
        ))
        db.send_create_signal(u'atex_web', ['Dropbox'])

        # Adding model 'SpecificationGroup'
        db.create_table(u'atex_web_specificationgroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Category'], null=True)),
        ))
        db.send_create_signal(u'atex_web', ['SpecificationGroup'])

        # Adding model 'Specification'
        db.create_table(u'atex_web_specification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.SpecificationGroup'], null=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Category'], null=True)),
        ))
        db.send_create_signal(u'atex_web', ['Specification'])

        # Adding model 'ProductSpecification'
        db.create_table(u'atex_web_productspecification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Product'])),
            ('spec', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['atex_web.Specification'])),
            ('value', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'atex_web', ['ProductSpecification'])


    def backwards(self, orm):
        # Removing unique constraint on 'Hit', fields ['product', 'date']
        db.delete_unique(u'atex_web_hit', ['product_id', 'date'])

        # Deleting model 'Category'
        db.delete_table(u'atex_web_category')

        # Deleting model 'Product'
        db.delete_table(u'atex_web_product')

        # Deleting model 'Image'
        db.delete_table(u'atex_web_image')

        # Deleting model 'Hit'
        db.delete_table(u'atex_web_hit')

        # Deleting model 'CustomUser'
        db.delete_table(u'atex_web_customuser')

        # Removing M2M table for field groups on 'CustomUser'
        db.delete_table(db.shorten_name(u'atex_web_customuser_groups'))

        # Removing M2M table for field user_permissions on 'CustomUser'
        db.delete_table(db.shorten_name(u'atex_web_customuser_user_permissions'))

        # Deleting model 'Cart'
        db.delete_table(u'atex_web_cart')

        # Deleting model 'CartProducts'
        db.delete_table(u'atex_web_cartproducts')

        # Deleting model 'Dropbox'
        db.delete_table(u'atex_web_dropbox')

        # Deleting model 'SpecificationGroup'
        db.delete_table(u'atex_web_specificationgroup')

        # Deleting model 'Specification'
        db.delete_table(u'atex_web_specification')

        # Deleting model 'ProductSpecification'
        db.delete_table(u'atex_web_productspecification')


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
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Category']", 'null': 'True'}),
            'specs_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'})
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
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['atex_web.Category']", 'null': 'True'}),
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
            'value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
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