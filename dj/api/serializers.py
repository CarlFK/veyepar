from rest_framework import serializers

from main.models import Client, Show, Episode

class PresenterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Episode
        fields = ('id', 'authors', 'name', 'conf_url')

class ShowSerializer(serializers.HyperlinkedModelSerializer):
    episode_set = PresenterSerializer(many=True)
    class Meta:
        model = Show
        fields = ('id', 'name', 'schedule_url', 
                'episode_set' )

class CSPSerializer(serializers.ModelSerializer):
    show_set = ShowSerializer(many=True)
    class Meta:
        model = Client
        fields = ('id', 'name', 
                'show_set')

