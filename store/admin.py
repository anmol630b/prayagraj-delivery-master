from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Product, Cart, Order, OrderItem, DeliveryAgent, DeliveryAssignment, ChatMessage


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')
    can_delete = False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'image_preview')
    search_fields = ('name',)

    def image_preview(self, obj):
        try:
            if obj.image:
                return format_html('<img src="{}" height="40" style="border-radius:6px"/>', obj.image.url)
        except:
            pass
        return '—'
    image_preview.short_description = 'Image'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'availability_badge', 'created_at')
    list_filter = ('is_available', 'category')
    search_fields = ('name', 'description')
    list_editable = ('price',)
    ordering = ('-created_at',)

    def availability_badge(self, obj):
        if obj.is_available:
            return mark_safe('<span style="background:#22c55e;color:white;padding:3px 10px;border-radius:12px;font-size:12px">✅ Available</span>')
        return mark_safe('<span style="background:#ef4444;color:white;padding:3px 10px;border-radius:12px;font-size:12px">❌ Unavailable</span>')
    availability_badge.short_description = 'Status'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status_badge', 'address_short', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'address')
    readonly_fields = ('user', 'total_price', 'created_at')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)
    actions = ['mark_confirmed', 'mark_out_for_delivery', 'mark_delivered', 'mark_cancelled']

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'confirmed': '#3b82f6',
            'out_for_delivery': '#f97316',
            'delivered': '#22c55e',
            'cancelled': '#ef4444',
        }
        icons = {
            'pending': '⏳',
            'confirmed': '✅',
            'out_for_delivery': '🚴',
            'delivered': '🎉',
            'cancelled': '❌',
        }
        color = colors.get(obj.status, '#888')
        icon = icons.get(obj.status, '')
        label = obj.status.replace('_', ' ').title()
        return mark_safe(f'<span style="background:{color};color:white;padding:3px 12px;border-radius:12px;font-size:12px">{icon} {label}</span>')
    status_badge.short_description = 'Status'

    def address_short(self, obj):
        return obj.address[:40] + '...' if len(obj.address) > 40 else obj.address
    address_short.short_description = 'Address'

    @admin.action(description='✅ Mark as Confirmed')
    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')

    @admin.action(description='🚴 Mark as Out for Delivery')
    def mark_out_for_delivery(self, request, queryset):
        queryset.update(status='out_for_delivery')

    @admin.action(description='🎉 Mark as Delivered')
    def mark_delivered(self, request, queryset):
        queryset.update(status='delivered')

    @admin.action(description='❌ Mark as Cancelled')
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')
    search_fields = ('order__id', 'product__name')


@admin.register(DeliveryAgent)
class DeliveryAgentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'availability_badge', 'current_location')
    list_filter = ('is_available',)
    search_fields = ('user__username', 'phone')

    def availability_badge(self, obj):
        if obj.is_available:
            return mark_safe('<span style="background:#22c55e;color:white;padding:3px 10px;border-radius:12px;font-size:12px">🟢 Available</span>')
        return mark_safe('<span style="background:#ef4444;color:white;padding:3px 10px;border-radius:12px;font-size:12px">🔴 Busy</span>')
    availability_badge.short_description = 'Status'


@admin.register(DeliveryAssignment)
class DeliveryAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'agent', 'assigned_at', 'delivered_at', 'duration')
    readonly_fields = ('assigned_at',)
    search_fields = ('order__id', 'agent__user__username')

    def duration(self, obj):
        if obj.delivered_at:
            diff = obj.delivered_at - obj.assigned_at
            mins = int(diff.total_seconds() / 60)
            return f'{mins} min'
        return '⏳ Pending'
    duration.short_description = 'Delivery Time'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_admin', 'created_at']
    list_filter = ['is_admin', 'user']
    ordering = ['-created_at']
