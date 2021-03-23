from django import forms


class UploadCSVForm(forms.Form):
    class_group = forms.IntegerField()
    csv_file = forms.FileField(widget=forms.FileInput(attrs={'accept': '.csv'}))
