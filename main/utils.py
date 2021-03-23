import csv
from io import StringIO

from django.contrib.auth.models import User

from main.models import StudentProfile, Class


def import_users(csv_file, class_group_id):
    class_group = Class.objects.get(id=class_group_id)

    file = csv_file.read().decode('utf-8')
    csv_data = csv.reader(StringIO(file), delimiter=',')
    line_count = 0
    failed_rows = []
    for row in csv_data:
        if len(row) != 5:
            line_count += 1
            failed_rows.append(line_count)
            continue

        username = row[0]
        password = row[1]
        first_name = row[2]
        last_name = row[3]
        year_of_study = row[4]

        try:
            user = User.objects.create(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            StudentProfile.objects.create(
                student=user,
                year_of_study=year_of_study,
                class_group=class_group
            )
        except Exception:
            line_count += 1
            failed_rows.append(line_count)
            continue
        line_count += 1

    return line_count, failed_rows
