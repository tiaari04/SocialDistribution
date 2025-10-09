from django.http import JsonResponse

def _not_implemented(endpoint_name):
	return JsonResponse({"detail": "not implemented", "endpoint": endpoint_name}, status=501)

# Authors
def api_authors_list(request):
	return _not_implemented("api_authors_list")

def api_author_detail(request, author_serial):
	return _not_implemented("api_author_detail")

def api_author_followers(request, author_serial):
	return _not_implemented("api_author_followers")

def api_author_follower_detail(request, author_serial, foreign_encoded):
	return _not_implemented("api_author_follower_detail")

def api_author_inbox(request, author_serial):
	return _not_implemented("api_author_inbox")

# Entries
def api_author_entries(request, author_serial):
	return _not_implemented("api_author_entries")

def api_author_entry_detail(request, author_serial, entry_serial):
	return _not_implemented("api_author_entry_detail")

def api_author_entry_image(request, author_serial, entry_serial):
	return _not_implemented("api_author_entry_image")

def api_entry_by_fqid(request, entry_fqid):
	return _not_implemented("api_entry_by_fqid")

def api_entry_image(request, entry_fqid):
	return _not_implemented("api_entry_image")

# Comments & Likes (per-entry serial)
def api_entry_comments(request, author_serial, entry_serial):
	return _not_implemented("api_entry_comments")

def api_entry_likes(request, author_serial, entry_serial):
	return _not_implemented("api_entry_likes")

# ENTRY FQID based endpoints
def api_entry_comments_by_fqid(request, entry_fqid):
	return _not_implemented("api_entry_comments_by_fqid")

def api_entry_likes_by_fqid(request, entry_fqid):
	return _not_implemented("api_entry_likes_by_fqid")

# Liked / Commented lists
def api_author_liked(request, author_serial):
	return _not_implemented("api_author_liked")

def api_author_commented(request, author_serial):
	return _not_implemented("api_author_commented")

# Comment detail and likes on comment
def api_entry_comment_detail(request, author_serial, entry_serial, comment_fqid):
	return _not_implemented("api_entry_comment_detail")

def api_entry_comment_likes(request, author_serial, entry_serial, comment_fqid):
	return _not_implemented("api_entry_comment_likes")

# Global FQID endpoints
def api_comment_by_fqid(request, comment_fqid):
	return _not_implemented("api_comment_by_fqid")

def api_like_by_fqid(request, like_fqid):
	return _not_implemented("api_like_by_fqid")

# Stream & public
def api_stream(request):
	return _not_implemented("api_stream")

def api_public_entries(request):
	return _not_implemented("api_public_entries")

# Additional stubs for FQID/serial lookups
def api_author_by_fqid(request, author_fqid):
	return _not_implemented("api_author_by_fqid")

def api_author_by_fqid_liked(request, author_fqid):
	return _not_implemented("api_author_by_fqid_liked")

def api_author_by_fqid_commented(request, author_fqid):
	return _not_implemented("api_author_by_fqid_commented")

def api_author_liked_detail(request, author_serial, like_serial):
	return _not_implemented("api_author_liked_detail")

def api_author_commented_detail(request, author_serial, comment_serial):
	return _not_implemented("api_author_commented_detail")