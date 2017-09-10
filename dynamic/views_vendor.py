import json
from django.template.context import RequestContext
from django.views.generic import View
from django.views.generic.edit import (CreateView, UpdateView, 
                                       DeleteView, View)
from django.views.generic import ListView,DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect,render
from unityapp.forms import *
from unityapp.models import *
from unityapp.utils import *
from django.contrib import messages
from django.conf import settings
import os
from yafinder import filters, sorters
from yafinder.sorters import widgets
from django.forms.models import modelformset_factory
import pdf_utils
import decimal
from django.core import serializers
from django.utils import simplejson
from wkhtmltopdf.views import PDFTemplateResponse
from unityapp import email_helper
from django.core.urlresolvers import reverse, resolve, reverse_lazy
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from xlwt.Workbook import Workbook
from xlwt import easyxf
import copy,datetime
import tasks

style_date      = easyxf(num_format_str='dd/mm/yyyy')
style_int       = easyxf(num_format_str='#,##0')
style_money     = easyxf('font: bold on; pattern: pattern solid, fore-colour grey25', num_format_str='Rs#,##0.00')
style_price     = easyxf('align: horz right',num_format_str='#0.00')
style_field     = easyxf('align: horz left',num_format_str='#0.00')
style_title     = easyxf('font: bold on, height 250; align: horz center')
style_sub_title = easyxf('font: bold off, height 180; align: horz center')
style_opening_balance = easyxf('font: bold off, height 180; align: horz left')
style_closing_balance = easyxf('font: bold on, height 180; align: horz left')
style_center    = easyxf('align: horz center')
style_column_heading = easyxf('font:bold on; align:horiz center')
from sms_credit.models import *




class PurchaseQuotationCreate(CreateView):
    @method_decorator(login_required)
    @method_decorator(check_vendor_purchase_quotation_create())
    def dispatch(self, *args, **kwargs):
        return super(PurchaseQuotationCreate, self).dispatch(*args, **kwargs)
    template_name = "unityapp/vendor/purchase_quotation_create.html"
    def get(self,request,*args,**kwargs):
        form = PurchaseQuotationCreateForm()
        purchase_quotation_formset = PurchaseQuotationFormset()
        lst_levels = VendorPurchaseApproval.multihost.values_list('level','pk')
        return render(self.request, self.template_name, {'form': form,'purchase_quotation_formset':purchase_quotation_formset,'lst_levels':lst_levels})


    def post(self, request, *args, **kwargs):
        purchase_quotation_form = PurchaseQuotationCreateForm(request.POST)
        purchase_formset = PurchaseQuotationFormset(request.POST,request.FILES)
        lst_levels = VendorPurchaseApproval.multihost.values_list('level','pk')
        if purchase_quotation_form.is_valid() and purchase_formset.is_valid():
            selected_levels = [int(level) for level in request.POST.getlist('level')]
            if not selected_levels:
                messages.error(request, "Approved levels required.")
                saved_levels = [int(level) for level in request.POST.getlist('level')]
                return render(self.request,self.template_name, {'form': purchase_quotation_form,'purchase_quotation_formset':purchase_formset,'lst_levels':lst_levels,'saved_levels':saved_levels})
            form = purchase_quotation_form.save(commit=False)
            form.site = request.site
            form.created_user = request.user
            form.number = get_next_doc_number('purchase_quotation')
            form.save()
            purchase_quotation_form.save_m2m()
            purchase_formset.instance = form
            purchase_formset.save()
            vendor_master = VendorPurchaseRequestMaster.multihost.get(pk=form.id)
            vendor_master.approval_levels = selected_levels
            vendor_master.save()
            ins_msg = VendorPurchaseRequestMessage()
            ins_msg.created_user = request.user
            ins_msg.purchase_request = vendor_master
            ins_msg.content = 'Created the request'
            ins_msg.save()
            return HttpResponseRedirect(reverse('unityapp.purchase_quotation_view',kwargs={'pk': form.id}))
        else:
            saved_levels = [int(level) for level in request.POST.getlist('level')]
            return render(self.request,self.template_name, {'form': purchase_quotation_form,'purchase_quotation_formset':purchase_formset,'lst_levels':lst_levels,'saved_levels':saved_levels})




class PurchaseQuotationUpdate(UpdateView):
    @method_decorator(login_required)
    @method_decorator(check_vendor_purchase_quotation_create())
    def dispatch(self, *args, **kwargs):
        return super(PurchaseQuotationUpdate, self).dispatch(*args, **kwargs)

    model = VendorPurchaseRequestMaster
    template_name = "unityapp/vendor/purchase_quotation_edit.html"

    def get(self, request, *args, **kwargs):
        form = PurchaseQuotationCreateForm(instance=self.get_object())
        purchase_quotation_formset = PurchaseQuotationEditFormset(instance=self.get_object())
        lst_levels = VendorPurchaseApproval.multihost.values_list('level','pk').order_by('-level')
        saved_levels = [obj.id for obj in self.get_object().approval_levels.all()]
        return render(self.request, self.template_name, {'form': form, 'purchase_quotation_formset': purchase_quotation_formset,'lst_levels':lst_levels,'saved_levels':saved_levels})

    def post(self, request, *args, **kwargs):
        request.POST._mutable = True
        dct = dict(request.POST)
        lst_ids = [val[:-3] for val in dct if val.startswith('vendorpurchaserequestdetails_set') and val.endswith('id')]
        lst_del_forms = []
        for ids in lst_ids:
            if '%s-vendor_description'%ids in dct:
                lst_del_forms.append('%s-vendor_description'%ids)
            if '%s-vendor_description'%ids not in dct:
                request.POST['%s-DELETE'%ids] = [u'on']

        if not lst_del_forms:
          messages.error(request, "At least one detail is required")
          return redirect('unityapp.purchase_quotation_update', pk=self.get_object().id)
        purchase_form = PurchaseQuotationCreateForm(request.POST,instance=self.get_object())
        purchase_quotation_formset = PurchaseQuotationEditFormset(request.POST,request.FILES,instance=self.get_object())
        lst_levels = VendorPurchaseApproval.multihost.values_list('level','pk').order_by('-level')
        if purchase_form.is_valid() and purchase_quotation_formset.is_valid():
            selected_levels = [int(level) for level in request.POST.getlist('level')]
            if not selected_levels:
                messages.error(request, "Approved levels required.")
                saved_levels = [int(level) for level in request.POST.getlist('level')]
                return render(self.request, self.template_name, {'form': purchase_form, 'purchase_quotation_formset': purchase_quotation_formset,'lst_levels':lst_levels,'saved_levels':saved_levels})

            form = purchase_form.save(commit=False)
            form.save()
            purchase_form.save_m2m()
            purchase_quotation_formset.instance = form
            purchase_quotation_formset.save()
            vendor_master = VendorPurchaseRequestMaster.multihost.get(pk=form.id)
            vendor_master.approval_levels = selected_levels
            vendor_master.save()
            ins_msg = VendorPurchaseRequestMessage()
            ins_msg.created_user = request.user
            ins_msg.purchase_request = vendor_master
            ins_msg.content = 'Updated the request'
            ins_msg.save()
            return HttpResponseRedirect(reverse('unityapp.purchase_quotation_view',kwargs={'pk': form.id}))
        else:
            saved_levels = [int(level) for level in request.POST.getlist('level')]
            return render(self.request, self.template_name, {'form': purchase_form, 'purchase_quotation_formset': purchase_quotation_formset,'lst_levels':lst_levels,'saved_levels':saved_levels})


class PurchaseQuotationView(DetailView):
    model = VendorPurchaseRequestMaster
    template_name = "unityapp/vendor/purchase_quotation_detail.html"

    @method_decorator(login_required)
    @method_decorator(check_vendor_purchase_quotation_previlege())
    def dispatch(self, *args, **kwargs):
        return super(PurchaseQuotationView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PurchaseQuotationView, self).get_context_data(**kwargs)
        purchase_quotation_details = VendorPurchaseRequestDetails.objects.filter(purchase_request=self.get_object())
        vendor_request_message = VendorPurchaseRequestMessage.objects.filter(purchase_request=self.get_object()).order_by('created_date')
        context['purchase_quotation_details'] = purchase_quotation_details
        context['vendor_request_message'] = vendor_request_message
        context['int_choosen_vendor'] = purchase_quotation_details.filter(choosen=True).count()
        vendor_purchase_approval = VendorPurchaseApproval.multihost.filter(users__in=[self.request.user.userprofile])
        vendor_purchase_approval_levels = [obj.level for obj in vendor_purchase_approval]
        approval_levels = [int(obj.level) for obj in self.get_object().approval_levels.all()]
        approval_levels.sort()
        context['first_level'] = str(approval_levels[0])
        context['vendor_purchase_approval_levels'] = vendor_purchase_approval_levels
        return context

@check_vendor_purchase_quotation_previlege()
def purchase_quotation_list(request, template_name='unityapp/vendor/purchase_quotation_list.html'):
    category = 'nonpaidlist'
    if 'category' in request.GET:
        category = request.GET['category']

    int_category = 1

    if category == 'escalated':
        int_category = 2
    elif category== 'approved':
        int_category = 3

    vendor_purchase_approval = VendorPurchaseApproval.multihost.filter(users__in=[request.user.userprofile])
    vendor_purchase_approval_levels = [obj.level for obj in vendor_purchase_approval]
    objects = []
    user_group = request.user.groups.all()[0].name

    if int_category == 1:
        if VendorPurchasePermission.multihost.filter(group__name__in=[user_group]).count():
            objects = VendorPurchaseRequestMaster.multihost.filter(Q(escalation_level__in=vendor_purchase_approval_levels,approved=False,deleted=False)|Q(escalation_level='0',approved=False,deleted=False)).order_by('-id')
        else:
            objects = VendorPurchaseRequestMaster.multihost.filter(escalation_level__in=vendor_purchase_approval_levels,approved=False,deleted=False).order_by('-id')
    
    elif int_category == 2:
        objects = VendorPurchaseRequestMaster.multihost.exclude(escalation_level__in=vendor_purchase_approval_levels).filter(approved=False,deleted=False).order_by('-id')
    else:
        objects = VendorPurchaseRequestMaster.multihost.filter(approved=True,deleted=False)
    
    sorter = sorters.Sorter((
        sorters.Field(label="No",  is_default=True, desc=True,callback=sorters.from_fields("number")),
        sorters.Field(label="Item Name",  is_default=True, desc=True,callback=sorters.from_fields("number")),
        sorters.Field(label="Quantity",  is_default=True, desc=True,callback=sorters.from_fields("number")),
        sorters.Field(label="Required date", callback=sorters.from_fields("required_date")),
        sorters.Field(label="Expense Account", callback=sorters.from_fields("expence_account__name")),
        sorters.Field(label="Escalation Level", callback=sorters.from_fields("escalation_level")),
        sorters.Field(label="", widget=widgets.Text),
        ), data=request.GET)
    

    if sorter.is_valid():
        if int_category == 1:
            objects = sorter.run(objects)
    else:
        return sorter.redirect()

    context = {
        'objects': objects,
        'category':int_category,
        'sorter':sorter,
        }
    return render_to_response(template_name, context, context_instance=RequestContext(request))

@check_vendor_purchase_quotation_previlege()
def vendor_purchase_quotation_edit(request, id=None, template_name='unityapp/vendor/purchase_quotation_vendor_edit.html'):
    try:
        object = VendorPurchaseRequestDetails.objects.get(pk=id)
    except ObjectDoesNotExist:
        raise Http404("Invalid Request")

    success = False
    if request.method == 'POST':
        form = PurchaseQuotationChangeVendor(request.POST,request.FILES,instance=object)
        if form.is_valid():
            ins_msg = VendorPurchaseRequestMessage()
            ins_msg.created_user = request.user
            ins_msg.purchase_request = object.purchase_request
            ins_msg.content = 'Updated the vendor details'
            ins_msg.save()
            form.save()
            success = True
    else:
        form = PurchaseQuotationChangeVendor(instance=object)
    context = {
        'form': form,
        'success': success
    }
    response = render_to_response(template_name, context, context_instance=RequestContext(request))
    response['AjaxContent'] = True
    return response

@check_vendor_purchase_quotation_previlege()
def vendor_purchase_quotation_approve(request, id=None, template_name='unityapp/vendor/purchase_quotation_vendor_approve.html'):
    try:
        vendor_purchase_approval = VendorPurchaseApproval.multihost.filter(users__in=[request.user.userprofile])
        vendor_purchase_approval_levels = [obj.level for obj in vendor_purchase_approval]
        object = VendorPurchaseRequestDetails.objects.get(pk=id,purchase_request__escalation_level__in=vendor_purchase_approval_levels)
    except ObjectDoesNotExist:
        raise Http404("Invalid Request")

    success = False
    if request.method == 'POST':
        form = PurchaseQuotationApprove(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            ins_msg = VendorPurchaseRequestMessage()
            ins_msg.created_user = request.user
            ins_msg.purchase_request = object.purchase_request
            level = object.purchase_request.escalation_level
            lst_levels = [int(ins_purchase.level) for ins_purchase in object.purchase_request.approval_levels.all()]
            lst_levels.sort()
            bln_last_level = False
            try:
                int_cur_index = lst_levels.index(int(level))
                if lst_levels[-1] <> int(level):
                    next_level = lst_levels[int_cur_index+1]
                else:
                    bln_last_level = True
                    next_level = int(level)
                    
            except:
                next_level = 1
            object.choosen = True
            VendorPurchaseRequestDetails.objects.filter(purchase_request=object.purchase_request).exclude(pk=object.id).update(choosen=False)
            object.purchase_request.escalation_level = str(next_level)
            if bln_last_level:
                object.purchase_request.approved = True
                ins_order = VendorPurchaseQuotationOrder()
                ins_order.site = request.site
                ins_order.number = get_next_doc_number('purchase_quotation_order')
                ins_order.purchase_request = object.purchase_request
                ins_order.save()

            object.purchase_request.save()
            object.save()
            str_msg = ''
            if not bln_last_level:
                str_msg = "Approved the vendor '%s' and opted for Escalation to level %s."%(object.vendor.name,str(next_level))
            else:
                str_msg = 'Approved the request.'
            ins_msg.content = str_msg+content
            ins_msg.save()
            tasks.notify_purchase_quotation.delay(object.purchase_request)
            success = True
    else:
        form = PurchaseQuotationApprove(initial={'master_id':object.id})
    context = {
        'form': form,
        'success': success,
        'title':'Approve Vendor'
    }
    response = render_to_response(template_name, context, context_instance=RequestContext(request))
    response['AjaxContent'] = True
    return response

@check_vendor_purchase_quotation_previlege()
def vendor_purchase_quotation_reject(request, id=None, template_name='unityapp/vendor/purchase_quotation_vendor_approve.html'):
    try:
        vendor_purchase_approval = VendorPurchaseApproval.multihost.filter(users__in=[request.user.userprofile])
        vendor_purchase_approval_levels = [obj.level for obj in vendor_purchase_approval]
        object = VendorPurchaseRequestDetails.objects.get(pk=id,purchase_request__escalation_level__in=vendor_purchase_approval_levels)
    except ObjectDoesNotExist:
        raise Http404("Invalid Request")

    success = False
    if request.method == 'POST':
        form = PurchaseQuotationApprove(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            ins_msg = VendorPurchaseRequestMessage()
            ins_msg.created_user = request.user
            ins_msg.purchase_request = object.purchase_request
            level = object.purchase_request.escalation_level
            lst_levels = [int(ins_purchase.level) for ins_purchase in object.purchase_request.approval_levels.all()]
            lst_levels.sort()
            bln_first_level = False
            try:
                int_cur_index = lst_levels.index(int(level))
                if lst_levels[0] <> int(level):
                    next_level = lst_levels[0]
                    #next_level = lst_levels[int_cur_index-1]
                else:
                    bln_first_level = True
                    next_level = int(level)
            except:
                next_level = 1

            if lst_levels[0] == next_level:
                object.choosen = False
                VendorPurchaseRequestDetails.objects.filter(purchase_request=object.purchase_request).update(choosen=False)
            object.purchase_request.escalation_level = str(next_level)
            object.purchase_request.save()
            object.save()
            str_msg = ''
            if not bln_first_level:
                str_msg = "Rejected the vendor '%s' and requested for resubmission to level %s."%(object.vendor.name,str(next_level))
            else:
                str_msg = "Requested to edit purchase quotation details."
                object.purchase_request.escalation_level = '0'
                object.purchase_request.save()
            ins_msg.content = str_msg+content
            ins_msg.save()
            tasks.notify_purchase_quotation.delay(object.purchase_request)
            success = True
    else:
        form = PurchaseQuotationApprove(initial={'master_id':object.id})
    context = {
        'form': form,
        'success': success,
        'title':'Reject Vendor'
    }
    response = render_to_response(template_name, context, context_instance=RequestContext(request))
    response['AjaxContent'] = True
    return response


@check_vendor_purchase_quotation_previlege()
def purchase_quotation_escalate(request):
    if request.method == 'POST':
        sel_id = request.POST.get('sel_id', None)
        if sel_id:
            try:
                object = VendorPurchaseRequestMaster.multihost.get(pk=sel_id,deleted=False)
            except ObjectDoesNotExist:
                raise Http404("Invalid Request")

            lst_levels = [int(ins_purchase.level) for ins_purchase in object.approval_levels.all()]
            lst_levels.sort()
            current_level = object.escalation_level
            try:
                if current_level in lst_levels:
                    int_cur_index = lst_levels.index(int(current_level))
                    if lst_levels[-1] <> int(current_level):
                        next_level = lst_levels[int_cur_index+1]
                    else:
                        bln_last_level = True
                        next_level = int(current_level)
                elif lst_levels:
                    next_level = int(lst_levels[0])
            except:
                next_level = 1

            object.escalation_level = str(next_level)
            ins_msg = VendorPurchaseRequestMessage()
            ins_msg.created_user = request.user
            ins_msg.purchase_request = object
            ins_msg.content = "Escalated to %s level"%str(next_level)
            ins_msg.save()
            object.save()
            tasks.notify_purchase_quotation.delay(object)
            messages.success(request, "Vendor Quotation Escalated Successfully.")
        return redirect('unityapp.purchase_quotation_list')
    else:
        raise Http404("Invalid Request")


@check_vendor_purchase_quotation_previlege()
def purchase_quotation_delete(request):
    if request.method == 'POST':
        sel_id = request.POST.get('sel_id', None)
        if sel_id:
            try:
                object = VendorPurchaseRequestMaster.multihost.get(pk=sel_id)
            except ObjectDoesNotExist:
                raise Http404("Invalid Request")

            object.deleted = True    
            ins_msg = VendorPurchaseRequestMessage()
            ins_msg.created_user = request.user
            ins_msg.purchase_request = object
            ins_msg.content = "Deleted the request"
            ins_msg.save()
            object.save()
            messages.success(request, "Vendor Quotation deleted Successfully.")
        return redirect('unityapp.purchase_quotation_list')
    else:
        raise Http404("Invalid Request")


class PurchaseQuotationOrderList(ListView):
    @method_decorator(login_required)
    @method_decorator(user_exist_menus_or_in_group('admin,manager,financier',menu1='Vendor,Purchase Orders'))
    def dispatch(self, *args, **kwargs):
        return super(PurchaseQuotationOrderList, self).dispatch(*args, **kwargs)

    model = VendorPurchaseQuotationOrder
    template_name = "unityapp/vendor/purchase_quotation_order_list.html"

    def get_context_data(self, **kwargs):
        context = super(PurchaseQuotationOrderList, self).get_context_data(**kwargs)
        category_type = 'undelivered'
        category = 1
        if 'category' in self.request.GET:
            category_type = self.request.GET['category']

        if category_type == 'undelivered':
            objects = self.model.multihost.filter(delivered=False).order_by('-id')
        else:
            category = 2
            objects = self.model.multihost.filter(delivered=True).order_by('-id')
            
        context['object_list'] = objects
        context['category'] = category
        return context


@user_exist_menus_or_in_group('manager,financier',menu1='Vendor,Book Expense')
def vendor_book_create_purchase_quotation(request,id=None,template_name='unityapp/vendor/vendor_purchase_quotation_book_create.html'):
    if not check_user_in_menusettings(request.user,'Vendor','Book Expense') and user_exist_in_site(request.user,request.site):
        raise Http404("Invalid Request")
    try:
        vendor_purchase_quotation = VendorPurchaseQuotationOrder.multihost.get(pk=id,delivered=False)
        obj_vendor_purchase_request_details = VendorPurchaseRequestDetails.objects.filter(purchase_request=vendor_purchase_quotation.purchase_request,choosen=True)
        if obj_vendor_purchase_request_details:obj_vendor_purchase_request_details=obj_vendor_purchase_request_details[0]
    except ObjectDoesNotExist:
        raise Http404("Invalid Request")

    if request.method == 'POST':
        form = VendorBookingForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_user = request.user
            obj.site = request.site
            obj.number = get_next_doc_number('vendor_booking_expense')
            bln_service_vat = form.cleaned_data['bln_service_vat']
            bln_tds = form.cleaned_data['bln_tds']
            total_credit_amount = obj.expense_amt - obj.deduction_amt
            total_debit_amount = obj.expense_amt - obj.deduction_amt
            tds_amount = form.cleaned_data['tds_amount'] or decimal.Decimal(0.0)
            tds_percentage = form.cleaned_data['tds_percentage'] or decimal.Decimal(0.0)
            obj.tds_amount = tds_amount
            obj.tds_percentage = tds_percentage
            tds_payable_amount = 0.0
            
            if bln_tds and tds_percentage:
                tds_payable_amount = total_credit_amount*tds_percentage/100
                pass
                
            if bln_tds and tds_amount:
                tds_payable_amount = tds_amount
                pass

            if bln_service_vat and obj.vat_or_service_amt:
                total_credit_amount += obj.vat_or_service_amt
                pass

            if bln_service_vat and obj.sbc_amt:
                total_credit_amount += obj.sbc_amt
                pass

            if bln_service_vat and obj.kkc_amt:
                total_credit_amount += obj.kkc_amt
                pass

            if tds_payable_amount:
                total_credit_amount -= tds_payable_amount
                obj.tds_payable_amount = tds_payable_amount
                pass


            if not bln_service_vat:
                obj.sbc_amt,obj.vat_or_service_amt,obj.kkc_amt = 0,0,0
                obj.service_tax_vat_account,obj.sbc_account,obj.kkc_account = None,None,None
                pass

            if not bln_tds:
                obj.tds_amount = decimal.Decimal(0.0)
                obj.tds_percentage = decimal.Decimal(0.0)
                obj.tds_payable_amount = decimal.Decimal(0.0)
                obj.tds_payable_account = None
        
            obj.save()
            group_name = request.user.groups.values()[0]['name']
            if group_name == 'financier' and accountant_approval(request.site):
                obj.approved = False
                obj.bln_cancelled = True
                obj.save()
            else:
                seq_no = 1
                je1 = JournalEntry()
                je1.seq_no = seq_no
                je1.site = request.site
                je1.value_date = obj.date
                je1.document = 'vendor_booking_expense'
                je1.document_num = obj.number
                je1.document_object = obj
                je1.description = obj.description
                je1.account = obj.expense_account
                je1.debit_amount = total_debit_amount
                je1.departments = obj.departments
                je1.save()

                if bln_service_vat and obj.vat_or_service_amt:
                    seq_no += 1
                    je2 = JournalEntry()
                    je2.seq_no = seq_no
                    je2.site = request.site
                    je2.value_date = obj.date
                    je2.document = 'vendor_booking_expense'
                    je2.document_num = obj.number
                    je2.document_object = obj
                    je2.description = 'Service/Vat added for '+' '+obj.description
                    je2.account = obj.service_tax_vat_account
                    je2.debit_amount = obj.vat_or_service_amt
                    je2.departments = obj.departments
                    je2.save()

                if bln_service_vat and obj.sbc_amt:
                    seq_no += 1
                    je3 = JournalEntry()
                    je3.seq_no = seq_no
                    je3.site = request.site
                    je3.value_date = obj.date
                    je3.document = 'vendor_booking_expense'
                    je3.document_num = obj.number
                    je3.document_object = obj
                    je3.description = 'SBC added for '+' '+obj.description
                    je3.account = obj.sbc_account
                    je3.debit_amount = obj.sbc_amt
                    je3.departments = obj.departments
                    je3.save()
                    pass

                if bln_service_vat and obj.kkc_amt:
                    seq_no += 1
                    je3 = JournalEntry()
                    je3.seq_no = seq_no
                    je3.site = request.site
                    je3.value_date = obj.date
                    je3.document = 'vendor_booking_expense'
                    je3.document_num = obj.number
                    je3.document_object = obj
                    je3.description = 'Krishi Kalyan Cess added for '+' '+obj.description
                    je3.account = obj.kkc_account
                    je3.debit_amount = obj.kkc_amt
                    je3.departments = obj.departments
                    je3.save()
                    pass


                seq_no += 1
                je4 = JournalEntry()
                je4.seq_no = seq_no
                je4.site = request.site
                je4.value_date = obj.date
                je4.document = 'vendor_booking_expense'
                je4.document_num = obj.number
                je4.document_object = obj
                je4.description = obj.description
                je4.account = obj.vendor.account
                je4.credit_amount = total_credit_amount
                je4.departments = obj.departments
                je4.save()

                if tds_payable_amount:
                    seq_no += 1
                    je4 = JournalEntry()
                    je4.seq_no = seq_no
                    je4.site = request.site
                    je4.value_date = obj.date
                    je4.document = 'vendor_booking_expense'
                    je4.document_num = obj.number
                    je4.document_object = obj
                    je4.description = 'TDS added for '+' '+obj.description
                    je4.account = obj.tds_payable_account
                    je4.credit_amount = tds_payable_amount
                    je4.departments = obj.departments
                    je4.save()
                    pass

            if vendor_purchase_quotation:
                vendor_purchase_quotation.delivered = True
                obj.purchase_order = vendor_purchase_quotation
                obj.save()
                ins_msg = VendorPurchaseRequestMessage()
                ins_msg.created_user = request.user
                ins_msg.purchase_request = vendor_purchase_quotation.purchase_request
                ins_msg.content = "Booked the expense"
                ins_msg.save()
                vendor_purchase_quotation.save()

            return redirect('unityapp.vendor_book_view',obj.id)
        else:
            messages.error(request, "Correct the displayed errors")
    else:
        quotation_values = {'expense_account' : vendor_purchase_quotation.purchase_request.expence_account ,
                            'vendor' : obj_vendor_purchase_request_details.vendor,
                            'expense_amt':obj_vendor_purchase_request_details.quotation_amount,
                            }
        form = VendorBookingForm(initial=quotation_values)

    context = {'form': form,'obj_vendor_purchase_request_details':obj_vendor_purchase_request_details,'vendor_purchase_quotation':vendor_purchase_quotation}
    return render_to_response(template_name,context, context_instance=RequestContext(request))



@check_vendor_purchase_quotation_previlege()
def vendor_purchase_quotation_comment(request, id=None, template_name='unityapp/vendor/purchase_quotation_vendor_approve.html'):
    try:
        object = VendorPurchaseRequestDetails.objects.get(pk=id)
    except ObjectDoesNotExist:
        raise Http404("Invalid Request")

    success = False
    if request.method == 'POST':
        form = PurchaseQuotationApprove(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            ins_msg = VendorDetailsMessage()
            ins_msg.created_user = request.user
            ins_msg.purchase_detail = object
            ins_msg.content = content
            ins_msg.save()
            success = True
    else:
        form = PurchaseQuotationApprove(initial={'master_id':object.id})
    context = {
        'form': form,
        'success': success,
        'title':'Comment Vendor'
    }
    response = render_to_response(template_name, context, context_instance=RequestContext(request))
    response['AjaxContent'] = True
    return response




    









