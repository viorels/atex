#!/bin/sh

# add on_delete to migration files for Django 2.x ugrade

grep --color ForeignKey $1
perl -pi -e 's/( models.ForeignKey\(.*?)\)/\1, on_delete=models.CASCADE)/' $1
perl -pi -e 's/(=models.ForeignKey\(.*?)\)/\1, on_delete=django.db.models.deletion.CASCADE)/' $1
echo "DONE"
grep --color ForeignKey $1
