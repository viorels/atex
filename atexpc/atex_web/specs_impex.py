from xlrd import open_workbook, XL_CELL_NUMBER
from collections import OrderedDict
from django import db
from django.db.utils import DataError

from .ancora_api import AncoraAPI
from .models import Category, Product, Specification, ProductSpecification, SpecificationGroup

IGNORED_COLUMNS = ('Duplicate',)
MODEL_COLUMN = 'Model'
SPEC_GROUP_SEPARATOR = '|'
EPSILON = 0.001     # convert to int if smaller then that

def import_specs(fname):
    book = open_workbook(fname)
    for sheet in book.sheets():
        category = worksheet_category(sheet)
        print("Sheet %s: %s" % (category['name'], worksheet_columns(sheet).values()))
        product_specs = import_category_specs(sheet)
        update_db_specs(category['id'], product_specs)

def import_category_specs(sheet):
    """ Return specs['model']['spec_group|spec'] = value """
    columns = worksheet_columns(sheet)
    model_column = [i for i, name in columns.items() if name.lower() == MODEL_COLUMN.lower()]
    if model_column:
        model_column = model_column[0]
        for row in range(1, sheet.nrows):
            model = str(cell_value(sheet.cell(row, model_column)))
            if model:
                model_specs = OrderedDict((name, cell_value(sheet.cell(row, i)))
                                          for i, name in columns.items()
                                          if i != model_column)
                yield model, model_specs
    db.reset_queries()

def cell_value(cell):
    value = cell.value
    try:
        if cell.ctype == XL_CELL_NUMBER and value - int(value) < EPSILON:
            value = int(value)
    except ValueError:
        pass
    return value

def update_db_specs(category_id, product_specs):
    # TODO: cache spec_group and used NamedTouple instead of dictionary
    category = Category.objects.get(pk=category_id)
    clear_db_specs(category)
    for model, specs in product_specs:
        product_orm = Product.objects.filter(model=model)
        if product_orm.exists():
            product_orm = product_orm[0]
            for spec, value in specs.items():
                if value == '':
                    continue
                spec_group, spec_name, spec_format = parse_spec(spec)
                if spec_group:
                    spec_group_orm, created = SpecificationGroup.objects.get_or_create(name=spec_group,
                                                                                       category=category)
                else:
                    spec_group_orm = None
                spec_orm, created = Specification.objects.get_or_create(name=spec_name,
                                                                        category=category,
                                                                        group=spec_group_orm)
                # print('Product %s: %s = %s' % (product_orm, spec_orm, value))
                try:
                    product_spec, created = ProductSpecification.objects.get_or_create(product=product_orm,
                                                                                       spec=spec_orm,
                                                                                       value=value)
                except DataError as e:
                    print('*** ERROR: %s' % e)
                if not created:
                    pass    # update ?

def clear_db_specs(category):
    if category:
        for product in Product.objects.filter(category=category):
            product.specs.clear()
        Specification.objects.filter(category=category).delete()
        SpecificationGroup.objects.filter(category=category).delete()

def parse_spec(spec):
    if SPEC_GROUP_SEPARATOR in spec:
        spec_group, spec_name = spec.split('|', 1)
    else:
        spec_group, spec_name = None, spec
    spec_format = None  # could be something like 'Group|Spec(% units)'
    return spec_group, spec_name, spec_format

def worksheet_category(sheet):
    api = AncoraAPI()
    category_code, _ = sheet.name.split('-', 1)
    return api.categories.get_category_by_code(category_code)

def worksheet_columns(sheet):
    """ Return columns[col_number] = col_title """
    columns = {}
    header_row = 0
    for col in range(sheet.ncols):
        header = sheet.cell(header_row, col).value
        if header not in IGNORED_COLUMNS:
            columns[col] = header
    return columns
