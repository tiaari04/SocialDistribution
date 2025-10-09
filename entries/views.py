from django.http import HttpResponse, JsonResponse

def stream_home(request):
	return HttpResponse("stream home (not implemented)")

def public_entries(request):
	return HttpResponse("public entries (not implemented)")

def entry_create(request):
	return HttpResponse("entry create (not implemented)")

def entry_detail(request, entry_serial):
	return HttpResponse(f"entry detail {entry_serial} (not implemented)")

def entry_edit(request, entry_serial):
	return HttpResponse(f"entry edit {entry_serial} (not implemented)")
