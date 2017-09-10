import datetime, re, os
from django.contrib.auth.models import User, Group
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.aggregates import Sum
from django.dispatch.dispatcher import receiver
from django.core.exceptions import ValidationError
import os
from multihost.managers import MultiHostManager
from unityapp.utils import check_none
from ckeditor.fields import RichTextField
from tinymce.models import HTMLField
from geoposition.fields import GeopositionField
from assets.models import Assets
from django.core.files.images import get_image_dimensions
from geoposition import Geoposition
from decimal import Decimal
from PIL import Image as Img
import StringIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import os.path
from django.db import transaction
import reversion
from uuid import uuid4

def meeting_minute_folder(model, filename):
    return 'site/' + str(model.site.pk) + '/meeting/' + filename

'''
Valid formats for tenant photograph.
'''

def validate_photo_extension(value):
    if value:
        ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
        valid_extensions = ['.jpg','.jpeg','.png','.JPG','.gif','.bmp','.psd']
        if not ext in valid_extensions:
            raise ValidationError(u'Unsupported file extension.')

'''
This model carries information about login details for the users.
'''
class Login(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    login_name = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=75, blank=True, null=True)
    first_password = models.CharField(max_length=50)
    profile_image = models.ImageField(upload_to=profile_image_folder, null=True, blank=True, help_text="Size 500 x 70",
             )
    tower = models.CharField(max_length=100,default='')
    user = models.OneToOneField(User)
    site = models.ForeignKey(Site)
    objects = models.Manager()
    multihost = MultiHostManager()

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        with transaction.atomic(), reversion.create_revision():

            super(UserProfile, self).save(*args, **kwargs)

'''
This model is used for store the details about client site with the primary details like logo, created date, address, home page image, mail ID.
'''
class Settings(models.Model):
    site = models.OneToOneField(Site)
    caption = models.CharField(max_length=200, null=True, blank=True)
   
    locked = models.BooleanField(default=False)
    sms_enabled = models.BooleanField(default=False)
    sub_end_date = models.DateField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    logo = models.ImageField(upload_to=site_upload_folder, null=True, blank=True, help_text="Size 500 x 70",
             validators=[validate_photo_extension])
    map_url = models.CharField(max_length=400, null=True, blank=True)
    home_page_image = models.ImageField(upload_to=site_upload_folder, null=True, blank=True, help_text="Width 600")
    home_page_content = models.TextField(null=True, blank=True)
    reply_email = models.EmailField(null=True, blank=True)
    email_signature = models.CharField(max_length=500, null=True, blank=True)
    financial_year = models.ForeignKey(FinancialYear, null=True, on_delete=models.SET_NULL)
    dues_statement_message = RichTextField(null=True,blank=True)
    dues_receipt_message = RichTextField(null=True, blank=True)
    
    ad_image = models.ImageField(max_length=500, upload_to=site_upload_folder, null=True, blank=True, help_text="Advertisement Image to be displayed in Dues Statement and Dues Receipt. Size 900 x 300, Maximum 5MB.",
                 validators=[validate_photo_extension])
   
    dues_warning_message = RichTextField(null=True,blank=True)
    
    advertisement_image = models.ImageField(max_length=500, upload_to=site_upload_folder, null=True, blank=True, help_text="Advertisement Image to be displayed in Dues Statement and Dues Receipt. Size 900 x 300, Maximum 5MB.",
                 validators=[validate_photo_extension])
    inst_code = models.CharField(max_length=50, null=True, blank=True)
   

    def __unicode__(self):
        return self.site.domain

   


    def save(self, *args, **kwargs):
        with transaction.atomic(), reversion.create_revision():
            if self.home_page_image :
                try:
                    img = Img.open(StringIO.StringIO(self.home_page_image.read()))
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    output = StringIO.StringIO()
                    img.save(output, format='JPEG', quality=30)
                    output.seek(0)

                    self.home_page_image= InMemoryUploadedFile(output,'ImageField', "%s.jpg" %self.home_page_image.name.split('.')[0], 'image/jpeg', output.len, None)
                except:
                    pass

           

            super(SiteProfile, self).save(*args, **kwargs)


class Permission(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(null=True)
    approved = models.BooleanField(default=False)
    user = models.ForeignKey(User)
    document_object = generic.GenericForeignKey()
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    objects = models.Manager()
    




class Transaction(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(null=True)
    created_user = models.ForeignKey(User, null=True, related_name='journalvoucher_created')
    updated_user = models.ForeignKey(User, null=True, related_name='journalvoucher_updated')
    date = models.DateField(null=True)
    number = models.IntegerField(null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reference = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=250, null=True)
    deleted = models.BooleanField(default=False)
    debit_account = models.ForeignKey(Account, related_name="debit")
    credit_account = models.ForeignKey(Account, related_name="credit")
    sys_gen = models.BooleanField(default=False)
    approved = models.BooleanField(default=True)
    approval_users = generic.GenericRelation(Permission)
    site = models.ForeignKey(Site)
    objects = models.Manager()
    multihost = MultiHostManager()

        




class Master(models.Model):
    invoice_description = models.CharField(max_length=250, null=True)
    settle_from_advance = models.BooleanField(default=False)
    service_tax = models.BooleanField(default=False)
    service_tax_split_up = models.BooleanField(default=False)
    service_tax_head = models.ForeignKey(Account, null=True, blank=True)
    fine_setting = models.ForeignKey(FineSetting, null=True, on_delete=models.SET_NULL)
    enabled = models.BooleanField(default=True)
    auto_gen_enabled = models.BooleanField(default=False)
    auto_gen_day = models.PositiveIntegerField(null=True)
    auto_gen_last_day_of_month = models.BooleanField(default=False)
    auto_gen_days_to_pay = models.PositiveIntegerField(null=True)
    periodic_generation = models.BooleanField(default=False)
    next_periodic_date = models.DateField(null=True)
    periodic_month = models.PositiveIntegerField(null=True)
    type = models.CharField(max_length=30, choices=GROUP_CHARGE_SETTING_TYPE)
    invoice_footer_notes = models.TextField(null=True,blank=True)
    credit_account = models.ForeignKey(Account, related_name='groupchargesettingmaster_credit_account',null=True,blank=True)
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True,blank=True)
    credit_description = models.CharField(max_length=300, null=True)
    credit_tower = models.CharField(max_length=100,null=True,blank=True)
    credit_resident_type = models.CharField(max_length=15,default='',choices=(('','----'),('Owner', 'Owner'),('Tenant', 'Tenant'),('Multi Tenant', 'Multi Tenant'),('Vacant', 'Vacant')))
    include_previous_arrears = models.BooleanField(default=False)
    include_credit = models.BooleanField(default=True)
    online_acc_details = models.ForeignKey(OnlineAccountDetails,null=True,blank=True)
    site = models.ForeignKey(Site)
    objects = models.Manager()
    multihost = MultiHostManager()
    pass



class Details(models.Model):
    charge_item_description = models.CharField(max_length=250, null=True)
    bln_service_tax = models.BooleanField(default=True)
    charge_account = models.ForeignKey(Account, related_name='groupchargesettingdetails_charge_account')
    tower = models.CharField(max_length=100,null=True,blank=True)
    resident_type = models.CharField(max_length=15,default='',choices=(('','----'),('Owner', 'Owner'),('Tenant', 'Tenant'),('Multi Tenant', 'Multi Tenant'),('Vacant', 'Vacant')))
    group_charge_setting_master = models.ForeignKey(Master)
    type = models.CharField(max_length=30,default='general', choices=GROUP_CHARGE_SETTING_TYPE)
    
    def total_amount(self):
        if self.type == 'general' :
            result = self.groupchargesettingvalue_set.aggregate(Sum('amount'))
            return result['amount__sum']
        else:
            result = self.groupchargesettingsquarefeetbased_set.aggregate(Sum('amount'))
            return result['amount__sum']
            pass
        pass


class RequestMaster(models.Model):
    number = models.IntegerField(null=True)
    created_user = models.ForeignKey(User,null=True,blank=True)
    required_date = models.DateField()
    created_date = models.DateField(auto_now=True)
    ship_to = models.TextField()
    item_name = models.CharField(max_length=200)
    item_description = models.TextField()
    expence_account = models.ForeignKey(Account,null=True,blank=True)
    approval_levels = models.ManyToManyField(VendorPurchaseApproval,related_name='vendor_approval_levels',null=True,blank=True)
    escalation_level = models.CharField(default='0',max_length=20)
    quantity = models.IntegerField(default=1)
    approved = models.BooleanField(default=False)
    escalated_time = models.DateTimeField(null=True,blank=True)
    deleted = models.BooleanField(default=False)
    site = models.ForeignKey(Site)
    objects = models.Manager()
    multihost = MultiHostManager()

    def __unicode__(self):
        return str(self.number)


class RequestDetails(models.Model):
    purchase_request = models.ForeignKey(RequestMaster)
    vendor = models.ForeignKey(VendorMaster)
    vendor_description = models.CharField(max_length=300)
    quotation_amount = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    quotation_attachment = models.FileField(upload_to=vendor_quotation_folder, null=True, blank=True)
    choosen = models.BooleanField(default=False)
    def __unicode__(self):
        return self.purchase_request




