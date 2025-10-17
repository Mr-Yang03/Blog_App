from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Tự động tạo UserProfile khi User được tạo

    Signal này sẽ chạy mỗi khi:
    - Tạo user qua form register
    - Tạo superuser qua createsuperuser
    - Tạo user qua Django Admin
    - Tạo user qua Python shell

    Parameters:
        sender: Model class (User)
        instance: Instance của User vừa được save
        created: True nếu là tạo mới, False nếu là update
        **kwargs: Các arguments khác
    """
    if created:
        UserProfile.objects.create(user=instance)
        print(f"✅ UserProfile created for user: {instance.username}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Tự động save UserProfile khi User được save

    Đảm bảo UserProfile luôn được save khi User thay đổi
    """
    # Kiểm tra xem user có profile chưa
    if hasattr(instance, 'profile'):
        instance.profile.save()
