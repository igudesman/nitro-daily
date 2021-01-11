from django.shortcuts import render
from django.http import HttpResponse
from scraping.tasks import update_data
from scraping.models import Player

import pandas as pd


def homePageView(request):
    info = {'current_info': Player.objects.all()}
    
    if request.method == 'POST':
        # try:
            csv_file = request.FILES["csv_file"]
            if not csv_file.name.endswith('.csv'):
                print('Not csv!')
            if csv_file.multiple_chunks():
                print('Too long!')

            df = pd.read_csv(csv_file, index_col=False)
            df = df.to_dict()
            names = []
            for name in df['Name'].values():
                names.append(name)
            print('Starting')
            update_data.delay()
            # my_first_task.delay(names)
        # except Exception as e:
        #     pass

    return render(request, 'home.html', info)