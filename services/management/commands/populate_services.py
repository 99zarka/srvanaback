from django.core.management.base import BaseCommand
from services.models import ServiceCategory, Service
import decimal

class Command(BaseCommand):
    help = 'Populates the ServiceCategory and Service models with initial data.'

    def handle(self, *args, **options):
        # Service Categories and Services Data
        service_data = {
            'Home Repair': {
                'description': 'خدمات متعلقة بالصيانة العامة للمنزل والإصلاحات.',
                'arabic_name': 'صيانة منزلية',
                'services': [
                    {
                        'name': 'Plumbing Repair',
                        'arabic_name': 'إصلاح السباكة',
                        'description': 'إصلاح أنابيب المياه المتسربة، وتصريفات المياه المسدودة، وتصليح المراحيض.',
                        'service_type': 'Repair',
                        'base_inspection_fee': decimal.Decimal('50.00'),
                        'estimated_price_range_min': decimal.Decimal('100.00'),
                        'estimated_price_range_max': decimal.Decimal('500.00')
                    },
                    {
                        'name': 'Electrical Services',
                        'arabic_name': 'خدمات كهربائية',
                        'description': 'مشاكل الأسلاك، تركيب المقابس، إصلاح تركيبات الإضاءة.',
                        'service_type': 'Repair/Installation',
                        'base_inspection_fee': decimal.Decimal('60.00'),
                        'estimated_price_range_min': decimal.Decimal('120.00'),
                        'estimated_price_range_max': decimal.Decimal('600.00')
                    },
                    {
                        'name': 'HVAC Maintenance',
                        'arabic_name': 'صيانة مكيفات وتدفئة',
                        'description': 'فحص وإصلاح أنظمة تكييف الهواء والتدفئة.',
                        'service_type': 'Maintenance/Repair',
                        'base_inspection_fee': decimal.Decimal('75.00'),
                        'estimated_price_range_min': decimal.Decimal('150.00'),
                        'estimated_price_range_max': decimal.Decimal('800.00')
                    },
                    {
                        'name': 'Appliance Repair',
                        'arabic_name': 'إصلاح الأجهزة المنزلية',
                        'description': 'إصلاح الأجهزة المنزلية مثل الغسالات والثلاجات والأفران.',
                        'service_type': 'Repair',
                        'base_inspection_fee': decimal.Decimal('65.00'),
                        'estimated_price_range_min': decimal.Decimal('130.00'),
                        'estimated_price_range_max': decimal.Decimal('700.00')
                    },
                    {
                        'name': 'Painting Services',
                        'arabic_name': 'خدمات الدهانات',
                        'description': 'طلاء المنازل من الداخل والخارج.',
                        'service_type': 'Renovation',
                        'base_inspection_fee': decimal.Decimal('80.00'),
                        'estimated_price_range_min': decimal.Decimal('200.00'),
                        'estimated_price_range_max': decimal.Decimal('1500.00')
                    },
                    {
                        'name': 'Carpentry',
                        'arabic_name': 'نجارة',
                        'description': 'أعمال النجارة المخصصة، إصلاح الأثاث، تركيب الخزائن.',
                        'service_type': 'Installation/Repair',
                        'base_inspection_fee': decimal.Decimal('70.00'),
                        'estimated_price_range_min': decimal.Decimal('150.00'),
                        'estimated_price_range_max': decimal.Decimal('1200.00')
                    },
                    {
                        'name': 'Roofing Repair',
                        'arabic_name': 'إصلاح الأسقف',
                        'description': 'إصلاح التسربات، استبدال القرميد التالف، الصيانة العامة للأسقف.',
                        'service_type': 'Repair',
                        'base_inspection_fee': decimal.Decimal('90.00'),
                        'estimated_price_range_min': decimal.Decimal('300.00'),
                        'estimated_price_range_max': decimal.Decimal('2000.00')
                    },
                    {
                        'name': 'Gutter Cleaning',
                        'arabic_name': 'تنظيف المزاريب',
                        'description': 'تنظيف وتطهير المزاريب لمنع تلف المياه.',
                        'service_type': 'Maintenance',
                        'base_inspection_fee': decimal.Decimal('45.00'),
                        'estimated_price_range_min': decimal.Decimal('80.00'),
                        'estimated_price_range_max': decimal.Decimal('250.00')
                    }
                ]
            },
            'Automotive': {
                'description': 'خدمات صيانة وإصلاح المركبات.',
                'arabic_name': 'خدمات السيارات',
                'services': [
                    {
                        'name': 'Oil Change',
                        'arabic_name': 'تغيير الزيت',
                        'description': 'استبدال الزيت والفلتر القياسي.',
                        'service_type': 'Maintenance',
                        'base_inspection_fee': decimal.Decimal('30.00'),
                        'estimated_price_range_min': decimal.Decimal('50.00'),
                        'estimated_price_range_max': decimal.Decimal('100.00')
                    },
                    {
                        'name': 'Brake Inspection & Repair',
                        'arabic_name': 'فحص وإصلاح الفرامل',
                        'description': 'فحص تيل الفرامل، السائل، وإصلاح أنظمة الفرامل.',
                        'service_type': 'Inspection/Repair',
                        'base_inspection_fee': decimal.Decimal('40.00'),
                        'estimated_price_range_min': decimal.Decimal('100.00'),
                        'estimated_price_range_max': decimal.Decimal('400.00')
                    },
                    {
                        'name': 'Tire Rotation & Balance',
                        'arabic_name': 'تدوير وإتزان الإطارات',
                        'description': 'تدوير وإتزان الإطارات لضمان تآكل متساوي.',
                        'service_type': 'Maintenance',
                        'base_inspection_fee': decimal.Decimal('25.00'),
                        'estimated_price_range_min': decimal.Decimal('40.00'),
                        'estimated_price_range_max': decimal.Decimal('80.00')
                    },
                    {
                        'name': 'Battery Replacement',
                        'arabic_name': 'استبدال البطارية',
                        'description': 'فحص واستبدال بطاريات السيارات.',
                        'service_type': 'Repair/Installation',
                        'base_inspection_fee': decimal.Decimal('20.00'),
                        'estimated_price_range_min': decimal.Decimal('70.00'),
                        'estimated_price_range_max': decimal.Decimal('200.00')
                    },
                    {
                        'name': 'Diagnostic Services',
                        'arabic_name': 'خدمات التشخيص',
                        'description': 'استخدام أدوات التشخيص لتحديد مشاكل المحرك والنظام.',
                        'service_type': 'Inspection',
                        'base_inspection_fee': decimal.Decimal('50.00'),
                        'estimated_price_range_min': decimal.Decimal('80.00'),
                        'estimated_price_range_max': decimal.Decimal('250.00')
                    }
                ]
            },
            'IT Services': {
                'description': 'الدعم الفني والخدمات المتعلقة بالحاسوب.',
                'arabic_name': 'خدمات تقنية المعلومات',
                'services': [
                    {
                        'name': 'Computer Repair',
                        'arabic_name': 'إصلاح الحاسوب',
                        'description': 'تشخيص الأجهزة، استكشاف أخطاء البرامج، إزالة الفيروسات.',
                        'service_type': 'Repair',
                        'base_inspection_fee': decimal.Decimal('80.00'),
                        'estimated_price_range_min': decimal.Decimal('150.00'),
                        'estimated_price_range_max': decimal.Decimal('700.00')
                    },
                    {
                        'name': 'Network Setup',
                        'arabic_name': 'إعداد الشبكات',
                        'description': 'تركيب وتكوين الشبكات المنزلية أو للمكاتب الصغيرة.',
                        'service_type': 'Installation',
                        'base_inspection_fee': decimal.Decimal('100.00'),
                        'estimated_price_range_min': decimal.Decimal('200.00'),
                        'estimated_price_range_max': decimal.Decimal('1000.00')
                    },
                    {
                        'name': 'Data Recovery',
                        'arabic_name': 'استعادة البيانات',
                        'description': 'استعادة البيانات المفقودة أو التالفة من أجهزة التخزين المختلفة.',
                        'service_type': 'Repair',
                        'base_inspection_fee': decimal.Decimal('120.00'),
                        'estimated_price_range_min': decimal.Decimal('300.00'),
                        'estimated_price_range_max': decimal.Decimal('1500.00')
                    },
                    {
                        'name': 'Software Installation & Support',
                        'arabic_name': 'تثبيت ودعم البرمجيات',
                        'description': 'تثبيت أنظمة التشغيل والتطبيقات، وتقديم الدعم الفني.',
                        'service_type': 'Installation/Support',
                        'base_inspection_fee': decimal.Decimal('70.00'),
                        'estimated_price_range_min': decimal.Decimal('100.00'),
                        'estimated_price_range_max': decimal.Decimal('500.00')
                    }
                ]
            },
            'Cleaning Services': {
                'description': 'خدمات تنظيف احترافية للمنازل والمكاتب.',
                'arabic_name': 'خدمات التنظيف',
                'services': [
                    {
                        'name': 'Deep Cleaning',
                        'arabic_name': 'تنظيف عميق',
                        'description': 'تنظيف شامل للمساحات السكنية أو التجارية.',
                        'service_type': 'Cleaning',
                        'base_inspection_fee': decimal.Decimal('100.00'),
                        'estimated_price_range_min': decimal.Decimal('200.00'),
                        'estimated_price_range_max': decimal.Decimal('800.00')
                    },
                    {
                        'name': 'Carpet Cleaning',
                        'arabic_name': 'تنظيف السجاد',
                        'description': 'تنظيف احترافي للسجاد والموكيت.',
                        'service_type': 'Cleaning',
                        'base_inspection_fee': decimal.Decimal('70.00'),
                        'estimated_price_range_min': decimal.Decimal('150.00'),
                        'estimated_price_range_max': decimal.Decimal('600.00')
                    }
                ]
            },
            'Gardening & Landscaping': {
                'description': 'صيانة خارجية وتصميم حدائق.',
                'arabic_name': 'الحدائق وتنسيق المناظر الطبيعية',
                'services': [
                    {
                        'name': 'Lawn Mowing & Maintenance',
                        'arabic_name': 'قص وصيانة العشب',
                        'description': 'عناية منتظمة بالعشب، بما في ذلك القص، والتشذيب، والتحديد.',
                        'service_type': 'Maintenance',
                        'base_inspection_fee': decimal.Decimal('40.00'),
                        'estimated_price_range_min': decimal.Decimal('60.00'),
                        'estimated_price_range_max': decimal.Decimal('200.00')
                    },
                    {
                        'name': 'Tree Trimming',
                        'arabic_name': 'تقليم الأشجار',
                        'description': 'تقليم وتشذيب الأشجار للحفاظ على صحتها وجمالها.',
                        'service_type': 'Maintenance',
                        'base_inspection_fee': decimal.Decimal('80.00'),
                        'estimated_price_range_min': decimal.Decimal('150.00'),
                        'estimated_price_range_max': decimal.Decimal('700.00')
                    }
                ]
            }
        }

        self.stdout.write(self.style.MIGRATE_HEADING("Populating Service Categories and Services..."))

        for category_name, category_data in service_data.items():
            category, created = ServiceCategory.objects.update_or_create(
                category_name=category_name,
                defaults={
                    'description': category_data['description'],
                    'arabic_name': category_data['arabic_name']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created ServiceCategory: {category_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'ServiceCategory already exists: {category_name}'))

            for service_details in category_data['services']:
                service, created = Service.objects.update_or_create(
                    category=category,
                    service_name=service_details['name'],
                    defaults={
                        'description': service_details['description'],
                        'arabic_name': service_details['arabic_name'],
                        'service_type': service_details['service_type'],
                        'base_inspection_fee': service_details['base_inspection_fee'],
                        'estimated_price_range_min': service_details.get('estimated_price_range_min'),
                        'estimated_price_range_max': service_details.get('estimated_price_range_max'),
                        'emergency_surcharge_percentage': service_details.get('emergency_surcharge_percentage', decimal.Decimal('0.00'))
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'    Successfully created Service: {service.service_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'    Service already exists: {service.service_name}'))

        self.stdout.write(self.style.MIGRATE_HEADING("Service population complete."))
