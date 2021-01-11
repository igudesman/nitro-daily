from django.db import models


class Player(models.Model):
    name = models.TextField()
    team = models.TextField()
    role = models.TextField()
    goal = models.FloatField()
    assist = models.FloatField()
    cs = models.FloatField()

    bc = models.FloatField()
    npxg = models.FloatField()
    xg = models.FloatField()
    bcc = models.FloatField()
    xa = models.FloatField()

    sixty = models.FloatField()
    ninety = models.FloatField()
    total_goals = models.IntegerField()
    total_pen = models.IntegerField()
    total_pas = models.IntegerField()
    total_yellow = models.IntegerField()
    total_red = models.IntegerField()


class Prediction(models.Model):
    name = models.TextField()
    team = models.TextField()
    role = models.TextField()
    goal = models.FloatField()
    assist = models.FloatField()
    cs = models.FloatField()
    date = models.TextField()


class Sport(models.Model):
    name = models.TextField()
    sixty = models.FloatField()
    ninety = models.FloatField()
    total_goals = models.IntegerField()
    total_pen = models.IntegerField()
    total_pas = models.IntegerField()
    total_yellow = models.IntegerField()
    total_red = models.IntegerField()
    date = models.TextField()


class Opta(models.Model):
    name = models.TextField()
    team = models.TextField()
    bc = models.FloatField()
    npxg = models.FloatField()
    xg = models.FloatField()
    bcc = models.FloatField()
    xa = models.FloatField()
    date = models.TextField()
    