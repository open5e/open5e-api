# https://drf-spectacular.readthedocs.io/en/latest/customization.html#step-7-preprocessing-hooks
def custom_preprocessing_hook(endpoints):
	# Only show api v2 endpoints
	endpoints = [
		(path, path_regex, method, callback) 
		for (path, path_regex, method, callback) in endpoints 
		if path.startswith('/v2')
	]

	return endpoints


# https://drf-spectacular.readthedocs.io/en/latest/customization.html#step-6-postprocessing-hooks
# def custom_postprocessing_hook(result, generator, request, public):
# 	return result