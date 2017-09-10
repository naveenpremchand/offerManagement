import datetime, re
from django.core.validators import validate_email, RegexValidator
from django.db.models.query_utils import Q
from django.forms import *
from django.forms.models import *
from django.forms.fields import *
from django.forms.widgets import *
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.contrib.auth.models import Group
from django.forms.models import  BaseFormSet, inlineformset_factory
from django.db.models import Q
from unityapp.models import *
from assets.models import *
import inspect
import fine_methods
from ckeditor.widgets import CKEditorWidget
from tinymce.widgets import TinyMCE
from django.contrib.sites.models import Site as gallery_site
from django.utils import timezone
from datetimewidget.widgets import DateTimeWidget, DateWidget, TimeWidget
from datetime import date
import datetime
from django.forms.widgets import Input
from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from sms_credit.models import *
import copy
from dateutil.relativedelta import relativedelta
from realestate.forms import FURNISHING_STATUS,TRANSACTION_TYPE_CHOICES,AVAILABILITY_CHOICES,AD_OBJ


    
class PurchaseQuotationCreateForm(ModelForm):
    item_description = CharField(widget=Textarea(attrs={'class':'form-control','style' : "border-radius:0px; height:150px;  resize:none;"}), help_text="")
    item_name = CharField(required=True,widget = forms.TextInput(attrs={'class':'form-control'}))
    quantity =  IntegerField(required=True,label="Quantity",initial=0, widget = TextInput(attrs={"class": "form-control", "style":"width:150px;",'type':'number'}))
    def __init__(self, *args, **kwargs):
        super(PurchaseQuotationCreateForm, self).__init__(*args, **kwargs)
        self.fields['expence_account'].required = True
        self.fields['expence_account'].queryset =Account.multihost.filter\
            (subCategory__account_categories__name__in=('expense','asset'),house=False,transaction=False).order_by('name')

    class Meta:
        model = VendorPurchaseRequestMaster
        fields = ('item_name','item_description','quantity','required_date','ship_to','expence_account')
        widgets = {
            'required_date': DateWidget(attrs={'id': "required_date"}, usel10n=True,
                                            bootstrap_version=3,options={'startDate':(datetime.date.today()+ datetime.timedelta(days=1)).strftime('%Y-%m-%d')})
        }


class PurchaseQuotationDetailsForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PurchaseQuotationDetailsForm, self).__init__(*args, **kwargs)
        self.fields['vendor'].queryset  = VendorMaster.multihost.all()
        for str_field in ('vendor','vendor_description','quotation_amount') :
            self.fields[str_field].required = True
            self.fields[str_field].widget.attrs.update({'class' : 'form-control'})
        
    class Meta:
        model = VendorPurchaseRequestDetails
        fields = ('vendor','vendor_description','quotation_amount','quotation_attachment')



        


PurchaseQuotationFormset = inlineformset_factory(VendorPurchaseRequestMaster, VendorPurchaseRequestDetails, form=PurchaseQuotationDetailsForm,
                                      extra=1,can_delete=True)

PurchaseQuotationEditFormset = inlineformset_factory(VendorPurchaseRequestMaster, VendorPurchaseRequestDetails, form=PurchaseQuotationDetailsForm,
                                      extra=0,can_delete=True)


# user_levels = [(str(level),str(level))  for level in range(1,101) ]
# tpl_user_level = tuple(user_levels)
class PurchaseQuotationApprovalForm(ModelForm):
    name = CharField(required=True,max_length=200,label='Approval Level Name',widget=TextInput(attrs={'class':'form-control','placeholder':'Approval Name'}))
    level = IntegerField(min_value=0,label="Level",widget = NumberInput(attrs={"class": "form-control"}))
    #ChoiceField(required=False,choices=tpl_user_level,widget=Select(attrs={'class': "form-control"}))
    users = CharField(required=True,widget=TextInput(attrs={'id':'myAutocomplete'}))

    def __init__(self,  *args, **kwargs):
        super(PurchaseQuotationApprovalForm, self).__init__(*args, **kwargs)


    def clean_level(self):
        level = self.cleaned_data['level']
        if self.instance.pk:
            count = VendorPurchaseApproval.multihost.exclude(pk=self.instance.pk).filter(level=level).count()
        else:
            count = VendorPurchaseApproval.multihost.filter(level=level).count()
        if count <> 0:
            self._errors['level']=self.error_class(["Level already added.Please edit that to change further."])
        return level
       
    class Meta:
        model = VendorPurchaseApproval
        fields = ('name','level','users')



class PurchaseQuotationChangeVendor(ModelForm):
    quotation_attachment = FileField(required=False, label="Attachment")
    vendor_description = CharField(widget = Textarea(attrs={'style':"width:100%; height:50px;border:none;border-radius:3px;background-color:#eee"}))
    vendor = ModelChoiceField(queryset=None,  widget = Select(attrs={'class':"span3"}))
    quotation_amount = DecimalField(min_value=0, max_digits=10, decimal_places=2, widget = TextInput(attrs={'style':"text-align:right;"}))
    
    def __init__(self, *args, **kwargs):
            super(PurchaseQuotationChangeVendor, self).__init__(*args, **kwargs)
            self.fields['vendor'].queryset  = VendorMaster.multihost.all()
            
    class Meta:
            model = VendorPurchaseRequestDetails
            fields = ('vendor', 'vendor_description', 'quotation_amount','quotation_attachment')



class PurchaseQuotationApprove(Form):
    content =  CharField(label='Comment or Message', required=True, widget = Textarea(attrs={'style' : "border-radius:0px; height:150px;width:500px;resize:none;background-color: #eee; box-shadow:none;border:none;"}))
    master_id = CharField(widget = HiddenInput())




