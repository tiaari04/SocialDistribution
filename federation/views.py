from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def inbox(request):
    if request.method == 'POST':
        #data = json.loads(request.body)
        return JsonResponse({'status': 'success'}, status=200)
    elif request.method == 'GET':
        return JsonResponse({'message': 'Inbox endpoint'}, status=200)
    elif request.method == 'PATCH':
        return JsonResponse({'message': 'PATCH method not implemented yet'}, status=501)
    elif request.method == 'DELETE':
        return JsonResponse({'message': 'DELETE method not implemented yet'}, status=501)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)