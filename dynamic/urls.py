try:
    from django.conf.urls.defaults import *
except:
    from django.conf.urls import patterns, include, url

from django.views.generic import TemplateView


from unityapp.views_vendor import ( 
                                    PurchaseQuotationCreate,
                                    PurchaseQuotationUpdate,
                                    PurchaseQuotationView,
                                    PurchaseQuotationOrderList
                                    )




urlpatterns += patterns('unityapp.views_vendor',
    url(r'^purchase-quotation/create$', PurchaseQuotationCreate.as_view(), name='unityapp.purchase_quotation_request'),
    url(r'^purchase-quotation/list$', 'purchase_quotation_list', name='unityapp.purchase_quotation_list'),
    url(r'^purchase-quotation/update/(?P<pk>\d+)', PurchaseQuotationUpdate.as_view(), name='unityapp.purchase_quotation_update'),
    url(r'^purchase-quotation/view/(?P<pk>\d+)$', PurchaseQuotationView.as_view(), name='unityapp.purchase_quotation_view'),
    url(r'^purchase-quotation/vendor/edit/(?P<id>\d+)$', 'vendor_purchase_quotation_edit', name='unityapp.vendor_purchase_quotation_edit'),
    url(r'^purchase-quotation/vendor/approve/(?P<id>\d+)$', 'vendor_purchase_quotation_approve', name='unityapp.vendor_purchase_quotation_approve'),
    url(r'^purchase-quotation/vendor/reject/(?P<id>\d+)$', 'vendor_purchase_quotation_reject', name='unityapp.vendor_purchase_quotation_reject'),
    url(r'^purchase-quotation/escalate$', 'purchase_quotation_escalate', name='unityapp.purchase_quotation_escalate'),
    url(r'^purchase-quotation/delete$', 'purchase_quotation_delete', name='unityapp.purchase_quotation_delete'),
    url(r'^purchase_quotation_order/list$',PurchaseQuotationOrderList.as_view(), name='unityapp.purchase_quotation_order'),
    url(r'^vendor/book/purchasequotation/(?P<id>\d+)$', 'vendor_book_create_purchase_quotation', name='unityapp.vendor_book_create_purchase_quotation'),
    url(r'^purchase-quotation/vendor/comment/(?P<id>\d+)$', 'vendor_purchase_quotation_comment', name='unityapp.vendor_purchase_quotation_comment'),
    )


