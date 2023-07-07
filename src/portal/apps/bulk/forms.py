from django import forms


class CSVUploadForm(forms.Form):
    file = forms.FileField(label='CSVファイル', help_text='※拡張子csvのファイルをアップロードしてください。')
    
    def clean_file(self):
        file = self.cleaned_data['file']
        # 拡張子チェック
        if file.name.endswith('.csv'):
            return file
        else:
            raise forms.ValidationError('拡張子はcsvのみです')


class UserDeleteForm(forms.Form):
    del_email = forms.CharField(label='削除したいEmail', widget=forms.Textarea(attrs={"cols":60}))
