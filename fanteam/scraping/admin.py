from django.contrib import admin

from .models import Player
from .models import Prediction
from .models import Sport
from .models import Opta

admin.site.register(Player)
admin.site.register(Prediction)
admin.site.register(Sport)
admin.site.register(Opta)
