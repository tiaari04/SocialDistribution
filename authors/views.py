from django.http import HttpResponse

def author_list(request):
	return HttpResponse("author list (not implemented)")

def author_create(request):
	return HttpResponse("author create (not implemented)")

def author_detail(request, author_serial):
	return HttpResponse(f"author detail {author_serial} (not implemented)")

def author_edit(request, author_serial):
	return HttpResponse(f"author edit {author_serial} (not implemented)")

def author_entries_page(request, author_serial):
	return HttpResponse(f"author entries {author_serial} (not implemented)")

def author_followers_page(request, author_serial):
	return HttpResponse(f"author followers {author_serial} (not implemented)")

def follow_requests_page(request, author_serial):
	return HttpResponse(f"follow requests {author_serial} (not implemented)")
