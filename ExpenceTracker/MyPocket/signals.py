import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """ Creates or updates a UserProfile whenever a User is created/updated. """
    try:
        if created:
            # Create a new UserProfile if the user is new
            UserProfile.objects.create(user=instance)
            logger.info(f"UserProfile created for {instance.username}")
        else:
            # Update the UserProfile or create if it doesn't exist
            user_profile, created = UserProfile.objects.update_or_create(user=instance)
            if created:
                logger.info(f"UserProfile created for {instance.username}")
            else:
                logger.info(f"UserProfile updated for {instance.username}")
    except Exception as e:
        logger.error(f"Error in UserProfile signal: {str(e)}")
