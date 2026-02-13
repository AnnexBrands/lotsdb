from django import forms


class OverrideForm(forms.Form):
    qty = forms.IntegerField(label="Quantity", required=False)
    l = forms.DecimalField(label="Length", required=False, decimal_places=2, max_digits=10)
    w = forms.DecimalField(label="Width", required=False, decimal_places=2, max_digits=10)
    h = forms.DecimalField(label="Height", required=False, decimal_places=2, max_digits=10)
    wgt = forms.DecimalField(label="Weight", required=False, decimal_places=2, max_digits=10)
    value = forms.DecimalField(label="Value", required=False, decimal_places=2, max_digits=12)
    cpack = forms.CharField(label="Case/Pack", required=False, max_length=200)
    noted_conditions = forms.CharField(label="Conditions", required=False, widget=forms.Textarea(attrs={"rows": 2}))
    commodity_id = forms.IntegerField(label="Commodity ID", required=False)
    force_crate = forms.BooleanField(label="Force Crate", required=False)
    do_not_tip = forms.BooleanField(label="Do Not Tip", required=False)
