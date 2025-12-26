ARABIC_NOTIFICATIONS = {
    # Order-related notifications
    'order_created_title': 'تم إنشاء الطلب بنجاح',
    'order_created_message': 'تم إنشاء طلبك #{order_id} وهو في انتظار العروض.',
    'new_project_available_title': 'مشروع جديد متاح',
    'new_project_available_message': 'تم نشر مشروع جديد (#{order_id}) قد يثير اهتمامك!',
    'offer_declined_title': 'تم رفض العرض',
    'offer_declined_message': 'تم رفض عرضك للطلب #{order_id} من قبل العميل.',
    'offer_accepted_title': 'تم قبول العرض',
    'offer_accepted_message': 'تم قبول عرضك للطلب #{order_id}.',
    'offer_rejected_title': 'تم رفض العرض',
    'offer_rejected_message': 'تم رفض عرضك للطلب #{order_id}.',
    'offer_accepted_client_title': 'تم قبول العرض',
    'offer_accepted_client_message': 'لقد قبلت عرضًا للطلب #{order_id}.',
    'job_started_title': 'بدأ العمل',
    'job_started_message': 'بدأ الفني {technician_name} العمل على الطلب #{order_id}.',
    'job_done_title': 'تم وضع علامة على العمل كمنتهي',
    'job_done_message': 'وضع الفني {technician_name} علامة على الطلب #{order_id} كمنتهي. يرجى المراجعة وتحرير الأموال.',
    'funds_released_title': 'تم تحرير الأموال',
    'funds_released_message': 'قام العميل {client_name} بتحرير الأموال للطلب #{order_id}. تم تحديث رصيدك المعلق.',
    'dispute_initiated_title': 'تم بدء نزاع',
    'dispute_initiated_message': '{user_name} بدأ نزاعًا لطلبك #{order_id}.',
    'dispute_new_title': 'نزاع جديد',
    'dispute_new_message': 'تم بدء نزاع جديد للطلب #{order_id} من قبل {user_name}.',
    'order_cancelled_title': 'تم إلغاء الطلب',
    'new_offer_received_title': 'تم استلام عرض جديد',
    'new_offer_received_message': 'تم تقديم عرض جديد لطلبك #{order_id}.',
    
    # User/Technician notifications
    'new_direct_offer_title': 'تم استلام عرض مباشر جديد',
    'new_direct_offer_message': 'قام المستخدم {user_name} بعمل عرض مباشر للطلب #{order_id}.',
    'direct_offer_accepted_title': 'قبل الفني عرضك المباشر!',
    'direct_offer_accepted_message': 'قبل الفني {technician_name} عرضك المباشر للطلب #{order_id}. يرجى الانتقال إلى لوحة التحكم الخاصة بك لتأكيد العرض وتمويل الحجز لتأمين الخدمة.',
    'direct_offer_rejected_title': 'تم رفض عرضك المباشر',
    'direct_offer_rejected_message': 'رفض الفني {technician_name} عرضك المباشر للطلب #{order_id}. السبب: {reason}',
    
    # Dispute notifications
    'dispute_resolved_title': 'تم حل النزاع',
    'dispute_resolved_message': 'تم حل نزاعك للطلب #{order_id}. القرار: {resolution}. التفاصيل: {details}',
    'dispute_response_title': 'رد نزاع جديد',
    'dispute_response_message': 'تمت إضافة رد جديد إلى النزاع #{dispute_id} للطلب #{order_id}',
    
    # System notifications
    'auto_release_failed_title': 'فشل التحرير التلقائي',
    'auto_release_failed_message': 'فشل التحرير التلقائي للطلب #{order_id}: لا يوجد فني مخصص. يرجى الاتصال بالدعم.',
    'funds_auto_released_title': 'تم تحرير الأموال تلقائيًا',
    'funds_auto_released_message': 'تم تحرير الأموال للطلب #{order_id} تلقائيًا من قبل النظام. تم تحديث رصيدك المعلق.',
    'funds_auto_released_to_tech_message': 'تم تحرير الأموال للطلب #{order_id} إلى {technician_name}.',
    'system_error_title': 'خطأ في النظام',
    'system_error_message': 'حدث خطأ أثناء التحرير التلقائي للطلب #{order_id}: {error}',
    
    # Cancellation messages (using EGP)
    'order_cancelled_refund_message': 'تم إلغاء الطلب #{order_id} وتم إعادة {amount} جنيه مصري إلى رصيدك المتاح.',
    'order_cancelled_tech_message': 'تم إلغاء الطلب #{order_id} من قبل العميل/المسؤول. تم إعادة الأموال ({amount} جنيه مصري) إلى العميل.',
    'order_cancelled_no_funds_message': 'تم إلغاء الطلب #{order_id}.',
}
