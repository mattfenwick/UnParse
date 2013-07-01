echo 'before deleting anything:'

tree | grep pyc

rm unparse/*pyc
rm unparse/*/*pyc
rm unparse/*/*/*pyc

echo ''
echo 'after deleting stuff:'

tree | grep pyc

